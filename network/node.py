"""
QXChain Network Node - P2P Communication and Consensus
"""

import asyncio
import aiohttp
import json
import logging
from typing import List, Dict, Set, Optional
from datetime import datetime
import time

from ..core.blockchain import QXBlockchain
from ..core.block import Block, Transaction


class QXNode:
    """
    QXChain network node for P2P communication and consensus
    """
    
    def __init__(self, host: str = "localhost", port: int = 5000, node_id: str = None):
        self.host = host
        self.port = port
        self.node_id = node_id or f"node_{port}"
        self.blockchain = QXBlockchain()
        self.peers: Set[str] = set()
        self.is_mining = False
        self.sync_in_progress = False
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"QXNode-{self.port}")
        
    async def start(self):
        """Start the node server"""
        from aiohttp import web
        
        app = web.Application()
        
        # Add routes
        app.router.add_get('/info', self.get_node_info)
        app.router.add_get('/chain', self.get_chain)
        app.router.add_get('/peers', self.get_peers)
        app.router.add_post('/peers/add', self.add_peer)
        app.router.add_post('/blocks/receive', self.receive_block)
        app.router.add_post('/transactions/receive', self.receive_transaction)
        app.router.add_get('/sync', self.sync_blockchain)
        app.router.add_post('/mine/start', self.start_mining)
        app.router.add_post('/mine/stop', self.stop_mining)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        self.logger.info(f"Node {self.node_id} started on {self.host}:{self.port}")
        
        # Start background tasks
        asyncio.create_task(self.periodic_sync())
        asyncio.create_task(self.mining_loop())
        
    async def get_node_info(self, request):
        """Get node information"""
        return web.json_response({
            'node_id': self.node_id,
            'host': self.host,
            'port': self.port,
            'peers': list(self.peers),
            'blockchain_stats': self.blockchain.get_chain_stats(),
            'is_mining': self.is_mining,
            'timestamp': datetime.now().isoformat()
        })
    
    async def get_chain(self, request):
        """Get the blockchain"""
        return web.json_response({
            'chain': [block.to_dict() for block in self.blockchain.chain],
            'length': len(self.blockchain.chain)
        })
    
    async def get_peers(self, request):
        """Get connected peers"""
        return web.json_response({
            'peers': list(self.peers),
            'count': len(self.peers)
        })
    
    async def add_peer(self, request):
        """Add a new peer"""
        data = await request.json()
        peer_url = data.get('peer_url')
        
        if peer_url and peer_url not in self.peers:
            self.peers.add(peer_url)
            self.logger.info(f"Added peer: {peer_url}")
            
            # Sync with new peer
            await self.sync_with_peer(peer_url)
        
        return web.json_response({'message': 'Peer added successfully'})
    
    async def receive_block(self, request):
        """Receive a new block from a peer"""
        try:
            data = await request.json()
            block_data = data.get('block')
            
            if block_data:
                block = Block.from_dict(block_data)
                
                # Validate and add block
                if await self.validate_and_add_block(block):
                    self.logger.info(f"Received and added block {block.index}")
                    
                    # Broadcast to other peers
                    await self.broadcast_block(block, exclude_peer=request.remote)
                    
                    return web.json_response({'message': 'Block accepted'})
            
            return web.json_response({'error': 'Invalid block'}, status=400)
            
        except Exception as e:
            self.logger.error(f"Error receiving block: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def receive_transaction(self, request):
        """Receive a new transaction from a peer"""
        try:
            data = await request.json()
            tx_data = data.get('transaction')
            
            if tx_data:
                transaction = Transaction(**tx_data)
                
                if self.blockchain.add_transaction(transaction):
                    self.logger.info(f"Received transaction {transaction.transaction_hash}")
                    
                    # Broadcast to other peers
                    await self.broadcast_transaction(transaction, exclude_peer=request.remote)
                    
                    return web.json_response({'message': 'Transaction accepted'})
            
            return web.json_response({'error': 'Invalid transaction'}, status=400)
            
        except Exception as e:
            self.logger.error(f"Error receiving transaction: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def sync_blockchain(self, request):
        """Sync blockchain with peers"""
        if self.sync_in_progress:
            return web.json_response({'message': 'Sync already in progress'})
        
        self.sync_in_progress = True
        try:
            await self.sync_with_network()
            return web.json_response({'message': 'Sync completed'})
        finally:
            self.sync_in_progress = False
    
    async def start_mining(self, request):
        """Start mining"""
        data = await request.json()
        miner_address = data.get('miner_address')
        
        if not miner_address:
            return web.json_response({'error': 'Miner address required'}, status=400)
        
        self.miner_address = miner_address
        self.is_mining = True
        self.logger.info(f"Started mining for address: {miner_address}")
        
        return web.json_response({'message': 'Mining started'})
    
    async def stop_mining(self, request):
        """Stop mining"""
        self.is_mining = False
        self.logger.info("Stopped mining")
        
        return web.json_response({'message': 'Mining stopped'})
    
    async def validate_and_add_block(self, block: Block) -> bool:
        """Validate and add a block to the chain"""
        try:
            # Check if block is valid
            if not block.is_valid():
                return False
            
            # Check if block extends the current chain
            latest_block = self.blockchain.get_latest_block()
            if block.previous_hash != latest_block.block_hash:
                return False
            
            if block.index != latest_block.index + 1:
                return False
            
            # Add block to chain
            self.blockchain.chain.append(block)
            
            # Update balances
            for tx in block.transactions:
                if tx.sender != "0":
                    self.blockchain.balances[tx.sender] -= (tx.amount + tx.fee)
                self.blockchain.balances[tx.recipient] = self.blockchain.balances.get(tx.recipient, 0) + tx.amount
                
                if tx.fee > 0:
                    self.blockchain.balances[block.miner_address] = self.blockchain.balances.get(block.miner_address, 0) + tx.fee
            
            # Remove mined transactions from pending
            mined_hashes = {tx.transaction_hash for tx in block.transactions}
            self.blockchain.pending_transactions = [
                tx for tx in self.blockchain.pending_transactions 
                if tx.transaction_hash not in mined_hashes
            ]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating block: {e}")
            return False
    
    async def broadcast_block(self, block: Block, exclude_peer: str = None):
        """Broadcast a block to all peers"""
        message = {
            'block': block.to_dict()
        }
        
        for peer in self.peers:
            if peer != exclude_peer:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(f"{peer}/blocks/receive", json=message) as response:
                            if response.status == 200:
                                self.logger.debug(f"Broadcasted block to {peer}")
                except Exception as e:
                    self.logger.error(f"Failed to broadcast block to {peer}: {e}")
    
    async def broadcast_transaction(self, transaction: Transaction, exclude_peer: str = None):
        """Broadcast a transaction to all peers"""
        message = {
            'transaction': transaction.to_dict()
        }
        
        for peer in self.peers:
            if peer != exclude_peer:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(f"{peer}/transactions/receive", json=message) as response:
                            if response.status == 200:
                                self.logger.debug(f"Broadcasted transaction to {peer}")
                except Exception as e:
                    self.logger.error(f"Failed to broadcast transaction to {peer}: {e}")
    
    async def sync_with_network(self):
        """Sync blockchain with the network"""
        longest_chain = self.blockchain.chain
        longest_length = len(longest_chain)
        
        for peer in self.peers:
            try:
                chain = await self.get_peer_chain(peer)
                if chain and len(chain) > longest_length:
                    # Validate the longer chain
                    temp_blockchain = QXBlockchain()
                    temp_blockchain.chain = [Block.from_dict(block_data) for block_data in chain]
                    
                    if temp_blockchain.validate_chain():
                        longest_chain = temp_blockchain.chain
                        longest_length = len(longest_chain)
                        self.logger.info(f"Found longer valid chain from {peer}")
            
            except Exception as e:
                self.logger.error(f"Error syncing with peer {peer}: {e}")
        
        # Replace chain if we found a longer valid one
        if longest_length > len(self.blockchain.chain):
            self.blockchain.chain = longest_chain
            self.blockchain.recalculate_balances()
            self.logger.info(f"Blockchain updated to length {longest_length}")
    
    async def sync_with_peer(self, peer_url: str):
        """Sync with a specific peer"""
        try:
            chain = await self.get_peer_chain(peer_url)
            if chain and len(chain) > len(self.blockchain.chain):
                temp_blockchain = QXBlockchain()
                temp_blockchain.chain = [Block.from_dict(block_data) for block_data in chain]
                
                if temp_blockchain.validate_chain():
                    self.blockchain.chain = temp_blockchain.chain
                    self.blockchain.recalculate_balances()
                    self.logger.info(f"Synced with peer {peer_url}")
        
        except Exception as e:
            self.logger.error(f"Error syncing with peer {peer_url}: {e}")
    
    async def get_peer_chain(self, peer_url: str) -> Optional[List[Dict]]:
        """Get blockchain from a peer"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{peer_url}/chain") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('chain', [])
        except Exception as e:
            self.logger.error(f"Error getting chain from {peer_url}: {e}")
        
        return None
    
    async def periodic_sync(self):
        """Periodically sync with the network"""
        while True:
            try:
                await asyncio.sleep(30)  # Sync every 30 seconds
                if not self.sync_in_progress and self.peers:
                    await self.sync_with_network()
            except Exception as e:
                self.logger.error(f"Error in periodic sync: {e}")
    
    async def mining_loop(self):
        """Main mining loop"""
        while True:
            try:
                if self.is_mining and self.blockchain.pending_transactions and hasattr(self, 'miner_address'):
                    self.logger.info("Mining new block...")
                    
                    # Mine a new block
                    new_block = self.blockchain.mine_pending_transactions(self.miner_address)
                    
                    self.logger.info(f"Mined block {new_block.index} with hash {new_block.block_hash}")
                    
                    # Broadcast the new block
                    await self.broadcast_block(new_block)
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                self.logger.error(f"Error in mining loop: {e}")
                await asyncio.sleep(5)
    
    def connect_to_peers(self, peer_urls: List[str]):
        """Connect to initial peers"""
        for peer_url in peer_urls:
            self.peers.add(peer_url)
        
        self.logger.info(f"Connected to {len(peer_urls)} peers")
    
    async def shutdown(self):
        """Shutdown the node"""
        self.is_mining = False
        self.logger.info(f"Node {self.node_id} shutting down")