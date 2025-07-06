#!/usr/bin/env python3
"""
QXChain Node - Main entry point for running a blockchain node
"""

import argparse
import asyncio
import uvicorn
import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from api.server import app, blockchain, broadcast_update
from core.blockchain import QXBlockchain
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QXChainNode:
    """QXChain blockchain node"""
    
    def __init__(self, port: int = 8000, peers: list = None):
        self.port = port
        self.peers = peers or []
        self.blockchain = blockchain
        
    async def start(self):
        """Start the blockchain node"""
        logger.info(f"Starting QXChain node on port {self.port}")
        logger.info(f"Peers: {self.peers}")
        
        # Initialize blockchain if needed
        if len(self.blockchain.chain) == 1:  # Only genesis block
            logger.info("Blockchain initialized with genesis block")
            logger.info(f"Genesis block hash: {self.blockchain.chain[0].block_hash}")
        
        # Start the API server
        config = uvicorn.Config(
            app, 
            host="0.0.0.0", 
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        try:
            await server.serve()
        except KeyboardInterrupt:
            logger.info("Node shutdown requested")
        except Exception as e:
            logger.error(f"Node error: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="QXChain Quantum-Resistant Blockchain Node")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the node on")
    parser.add_argument("--peers", type=str, help="Comma-separated list of peer URLs")
    parser.add_argument("--create-wallet", type=str, help="Create a wallet with given user ID")
    parser.add_argument("--mine", action="store_true", help="Start mining mode")
    parser.add_argument("--miner-address", type=str, help="Miner address for mining rewards")
    
    args = parser.parse_args()
    
    # Parse peers
    peers = []
    if args.peers:
        peers = [peer.strip() for peer in args.peers.split(",")]
    
    # Create wallet if requested
    if args.create_wallet:
        print(f"Creating wallet for user: {args.create_wallet}")
        wallet = blockchain.create_wallet(args.create_wallet)
        if "error" in wallet:
            print(f"Error: {wallet['error']}")
        else:
            print(f"Wallet created successfully!")
            print(f"User ID: {wallet['user_id']}")
            print(f"Address: {wallet['address']}")
            print(f"Public Key (Kyber): {wallet['kyber_public_key'][:64]}...")
            print(f"Public Key (Signature): {wallet['signature_public_key'][:64]}...")
        return
    
    # Create node
    node = QXChainNode(port=args.port, peers=peers)
    
    # Start mining if requested
    if args.mine:
        if not args.miner_address:
            print("Error: --miner-address required for mining mode")
            return
        
        async def mining_loop():
            """Simple mining loop"""
            while True:
                try:
                    if blockchain.pending_transactions:
                        print(f"Mining block with {len(blockchain.pending_transactions)} transactions...")
                        block = blockchain.mine_pending_transactions(args.miner_address)
                        print(f"Block mined! Hash: {block.block_hash}")
                        
                        # Broadcast the new block
                        await broadcast_update({
                            "type": "block_mined",
                            "data": block.to_dict()
                        })
                    
                    await asyncio.sleep(10)  # Check for new transactions every 10 seconds
                except Exception as e:
                    print(f"Mining error: {e}")
                    await asyncio.sleep(5)
        
        # Start mining in background
        asyncio.create_task(mining_loop())
    
    # Start the node
    try:
        asyncio.run(node.start())
    except KeyboardInterrupt:
        print("\nShutting down node...")
    except Exception as e:
        print(f"Error starting node: {e}")

if __name__ == "__main__":
    main()