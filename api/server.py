"""
QXChain API Server
FastAPI-based REST API with WebSocket support for real-time updates
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import asyncio
import logging
from datetime import datetime

from ..core.blockchain import QXBlockchain
from ..core.block import Transaction

# Initialize FastAPI app
app = FastAPI(
    title="QXChain API",
    description="Quantum-Resistant Blockchain API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize blockchain
blockchain = QXBlockchain()

# WebSocket connections for real-time updates
websocket_connections: List[WebSocket] = []

# Pydantic models for API
class WalletCreate(BaseModel):
    user_id: str
    password: Optional[str] = None

class TransactionCreate(BaseModel):
    sender_user_id: str
    recipient_address: str
    amount: float
    fee: float = 0.01
    data: Optional[str] = None

class MineRequest(BaseModel):
    miner_address: str

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket manager
async def broadcast_update(message: Dict[str, Any]):
    """Broadcast update to all connected WebSocket clients"""
    if websocket_connections:
        disconnected = []
        for websocket in websocket_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except:
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for ws in disconnected:
            websocket_connections.remove(ws)

# API Routes

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "QXChain Quantum-Resistant Blockchain API", "version": "1.0.0"}

@app.get("/chain")
async def get_chain():
    """Get the full blockchain"""
    return {
        "chain": [block.to_dict() for block in blockchain.chain],
        "length": len(blockchain.chain)
    }

@app.get("/chain/stats")
async def get_chain_stats():
    """Get blockchain statistics"""
    return blockchain.get_chain_stats()

@app.get("/blocks/{block_index}")
async def get_block(block_index: int):
    """Get a specific block by index"""
    if block_index < 0 or block_index >= len(blockchain.chain):
        raise HTTPException(status_code=404, detail="Block not found")
    
    return blockchain.chain[block_index].to_dict()

@app.get("/blocks/latest")
async def get_latest_block():
    """Get the latest block"""
    return blockchain.get_latest_block().to_dict()

@app.post("/wallets")
async def create_wallet(wallet_data: WalletCreate):
    """Create a new quantum-resistant wallet"""
    try:
        result = blockchain.create_wallet(wallet_data.user_id, wallet_data.password)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Broadcast wallet creation
        await broadcast_update({
            "type": "wallet_created",
            "data": result,
            "timestamp": datetime.now().isoformat()
        })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/wallets/{user_id}")
async def get_wallet(user_id: str):
    """Get wallet information"""
    wallet = blockchain.get_wallet(user_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    # Don't return private keys in API response
    safe_wallet = {
        'user_id': wallet['user_id'],
        'address': wallet['address'],
        'kyber_public_key': wallet['kyber_public_key'],
        'signature_public_key': wallet['signature_public_key'],
        'created_at': wallet['created_at']
    }
    
    return safe_wallet

@app.get("/balance/{address}")
async def get_balance(address: str):
    """Get balance for an address"""
    balance = blockchain.get_balance(address)
    return {"address": address, "balance": balance}

@app.get("/transactions/history/{address}")
async def get_transaction_history(address: str):
    """Get transaction history for an address"""
    transactions = blockchain.get_transaction_history(address)
    return {
        "address": address,
        "transactions": [tx.to_dict() for tx in transactions],
        "count": len(transactions)
    }

@app.get("/transactions/pending")
async def get_pending_transactions():
    """Get pending transactions"""
    return {
        "pending_transactions": [tx.to_dict() for tx in blockchain.pending_transactions],
        "count": len(blockchain.pending_transactions)
    }

@app.post("/transactions")
async def create_transaction(tx_data: TransactionCreate):
    """Create a new transaction"""
    try:
        transaction = blockchain.create_transaction(
            sender_user_id=tx_data.sender_user_id,
            recipient_address=tx_data.recipient_address,
            amount=tx_data.amount,
            fee=tx_data.fee,
            data=tx_data.data
        )
        
        if blockchain.add_transaction(transaction):
            # Broadcast new transaction
            await broadcast_update({
                "type": "transaction_created",
                "data": transaction.to_dict(),
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "message": "Transaction created successfully",
                "transaction": transaction.to_dict()
            }
        else:
            raise HTTPException(status_code=400, detail="Transaction validation failed")
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mine")
async def mine_block(mine_request: MineRequest):
    """Mine a new block"""
    try:
        if not blockchain.pending_transactions:
            raise HTTPException(status_code=400, detail="No pending transactions to mine")
        
        # Mine the block
        new_block = blockchain.mine_pending_transactions(mine_request.miner_address)
        
        # Broadcast new block
        await broadcast_update({
            "type": "block_mined",
            "data": new_block.to_dict(),
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "message": "Block mined successfully",
            "block": new_block.to_dict()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/validate")
async def validate_chain():
    """Validate the blockchain"""
    is_valid = blockchain.validate_chain()
    return {
        "valid": is_valid,
        "message": "Blockchain is valid" if is_valid else "Blockchain validation failed"
    }

@app.get("/export")
async def export_blockchain():
    """Export blockchain as JSON"""
    try:
        chain_json = blockchain.export_chain()
        return {"blockchain": json.loads(chain_json)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/import")
async def import_blockchain(chain_data: Dict[str, Any]):
    """Import blockchain from JSON"""
    try:
        chain_json = json.dumps(chain_data.get("blockchain", {}))
        success = blockchain.import_chain(chain_json)
        
        if success:
            # Broadcast chain update
            await broadcast_update({
                "type": "chain_imported",
                "data": blockchain.get_chain_stats(),
                "timestamp": datetime.now().isoformat()
            })
            
            return {"message": "Blockchain imported successfully"}
        else:
            raise HTTPException(status_code=400, detail="Invalid blockchain data")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time blockchain updates"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        # Send initial blockchain stats
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "data": blockchain.get_chain_stats(),
            "timestamp": datetime.now().isoformat()
        }))
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
    
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "blockchain_stats": blockchain.get_chain_stats()
    }

# Serve static files (dashboard)
app.mount("/static", StaticFiles(directory="dashboard"), name="static")

@app.get("/dashboard")
async def serve_dashboard():
    """Serve the dashboard"""
    with open("dashboard/index.html", "r") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)