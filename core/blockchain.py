"""
QXChain Quantum-Resistant Blockchain Core
"""

import json
import time
import hashlib
from typing import List, Dict, Optional, Tuple
from .block import Block, Transaction
from ..crypto.kyber import Kyber1024
from ..crypto.quantum_signatures import QuantumSignature
import base58


class QXBlockchain:
    """
    Main blockchain class with quantum-resistant features
    """
    
    def __init__(self):
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.balances: Dict[str, float] = {}
        self.wallets: Dict[str, Dict] = {}  # user_id -> wallet_data
        self.nodes: set = set()
        self.difficulty = 4
        self.block_reward = 10.0
        self.max_transactions_per_block = 100
        
        # Create genesis block
        self.create_genesis_block()
    
    def create_genesis_block(self) -> None:
        """Create and add genesis block to chain"""
        genesis_block = Block.create_genesis_block()
        genesis_block.mine_block(difficulty=1)
        
        # Initialize genesis balance
        genesis_address = "QX1Genesis1111111111111111111111111"
        self.balances[genesis_address] = 42000000.0
        
        self.chain.append(genesis_block)
    
    def get_latest_block(self) -> Block:
        """Get the latest block in the chain"""
        return self.chain[-1]
    
    def create_wallet(self, user_id: str, password: Optional[str] = None) -> Dict:
        """Create a new quantum-resistant wallet"""
        if user_id in self.wallets:
            return {"error": "User ID already exists"}
        
        # Generate quantum-resistant key pairs
        # Kyber for key encapsulation
        kyber_pk, kyber_sk = Kyber1024.keygen()
        
        # Quantum signature keys
        sig_pk, sig_sk = QuantumSignature.keygen()
        
        # Generate address from public keys
        combined_pk = kyber_pk + sig_pk
        address_hash = hashlib.sha3_256(combined_pk).digest()[:20]
        address = "QX" + base58.b58encode_check(address_hash).decode()
        
        # Store wallet data
        wallet_data = {
            'user_id': user_id,
            'address': address,
            'kyber_public_key': kyber_pk.hex(),
            'kyber_private_key': kyber_sk.hex(),
            'signature_public_key': sig_pk.hex(),
            'signature_private_key': sig_sk.hex(),
            'created_at': time.time()
        }
        
        if password:
            # Hash password for storage
            password_hash = hashlib.sha3_256(password.encode()).hexdigest()
            wallet_data['password_hash'] = password_hash
        
        self.wallets[user_id] = wallet_data
        
        # Initialize balance
        self.balances[address] = 0.0
        
        return {
            'user_id': user_id,
            'address': address,
            'kyber_public_key': kyber_pk.hex(),
            'signature_public_key': sig_pk.hex()
        }
    
    def get_wallet(self, user_id: str) -> Optional[Dict]:
        """Get wallet information"""
        return self.wallets.get(user_id)
    
    def get_balance(self, address: str) -> float:
        """Get balance for an address"""
        return self.balances.get(address, 0.0)
    
    def create_transaction(self, sender_user_id: str, recipient_address: str, 
                         amount: float, fee: float = 0.01, data: str = None) -> Optional[Transaction]:
        """Create a new transaction"""
        wallet = self.get_wallet(sender_user_id)
        if not wallet:
            raise ValueError("Sender wallet not found")
        
        sender_address = wallet['address']
        sender_balance = self.get_balance(sender_address)
        
        if sender_balance < amount + fee:
            raise ValueError("Insufficient balance")
        
        # Create transaction
        transaction = Transaction(
            sender=sender_address,
            recipient=recipient_address,
            amount=amount,
            fee=fee,
            timestamp=time.time(),
            data=data
        )
        
        # Sign transaction
        private_key = bytes.fromhex(wallet['signature_private_key'])
        public_key = bytes.fromhex(wallet['signature_public_key'])
        
        transaction.public_key = public_key
        transaction.sign(private_key)
        
        return transaction
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """Add transaction to pending pool"""
        if not transaction.verify_signature():
            return False
        
        # Check if sender has sufficient balance
        sender_balance = self.get_balance(transaction.sender)
        if sender_balance < transaction.amount + transaction.fee:
            return False
        
        self.pending_transactions.append(transaction)
        return True
    
    def mine_pending_transactions(self, miner_address: str) -> Block:
        """Mine a new block with pending transactions"""
        # Select transactions for the block
        transactions_to_mine = self.pending_transactions[:self.max_transactions_per_block]
        
        # Add mining reward transaction
        reward_tx = Transaction(
            sender="0",  # System
            recipient=miner_address,
            amount=self.block_reward,
            fee=0.0,
            timestamp=time.time(),
            data="Mining reward"
        )
        transactions_to_mine.append(reward_tx)
        
        # Create new block
        new_block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            transactions=transactions_to_mine,
            previous_hash=self.get_latest_block().block_hash,
            difficulty=self.difficulty,
            miner_address=miner_address,
            block_reward=self.block_reward
        )
        
        # Mine the block
        new_block.mine_block()
        
        # Update balances
        for tx in transactions_to_mine:
            if tx.sender != "0":  # Not a reward transaction
                self.balances[tx.sender] -= (tx.amount + tx.fee)
            self.balances[tx.recipient] = self.balances.get(tx.recipient, 0) + tx.amount
            
            # Add fees to miner
            if tx.fee > 0:
                self.balances[miner_address] = self.balances.get(miner_address, 0) + tx.fee
        
        # Add block to chain
        self.chain.append(new_block)
        
        # Remove mined transactions from pending
        self.pending_transactions = self.pending_transactions[len(transactions_to_mine)-1:]
        
        # Adjust difficulty
        self.adjust_difficulty()
        
        return new_block
    
    def adjust_difficulty(self) -> None:
        """Adjust mining difficulty based on block time"""
        if len(self.chain) < 2:
            return
        
        # Target block time: 10 seconds
        target_time = 10.0
        
        # Look at last 10 blocks
        recent_blocks = self.chain[-10:] if len(self.chain) >= 10 else self.chain[1:]
        
        if len(recent_blocks) < 2:
            return
        
        time_taken = recent_blocks[-1].timestamp - recent_blocks[0].timestamp
        average_time = time_taken / (len(recent_blocks) - 1)
        
        if average_time < target_time * 0.5:
            self.difficulty += 1
        elif average_time > target_time * 2:
            self.difficulty = max(1, self.difficulty - 1)
    
    def validate_chain(self) -> bool:
        """Validate the entire blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Validate current block
            if not current_block.is_valid():
                return False
            
            # Check if current block points to previous block
            if current_block.previous_hash != previous_block.block_hash:
                return False
        
        return True
    
    def replace_chain(self, new_chain: List[Block]) -> bool:
        """Replace chain if new chain is longer and valid"""
        if len(new_chain) <= len(self.chain):
            return False
        
        # Validate new chain
        temp_blockchain = QXBlockchain()
        temp_blockchain.chain = new_chain
        
        if not temp_blockchain.validate_chain():
            return False
        
        # Replace chain and recalculate balances
        self.chain = new_chain
        self.recalculate_balances()
        return True
    
    def recalculate_balances(self) -> None:
        """Recalculate all balances from the blockchain"""
        self.balances = {}
        
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender != "0":  # Not a reward transaction
                    self.balances[tx.sender] = self.balances.get(tx.sender, 0) - (tx.amount + tx.fee)
                
                self.balances[tx.recipient] = self.balances.get(tx.recipient, 0) + tx.amount
                
                # Add fees to miner (if not genesis block)
                if block.index > 0 and tx.fee > 0:
                    self.balances[block.miner_address] = self.balances.get(block.miner_address, 0) + tx.fee
    
    def get_transaction_history(self, address: str) -> List[Transaction]:
        """Get transaction history for an address"""
        transactions = []
        
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == address or tx.recipient == address:
                    transactions.append(tx)
        
        return transactions
    
    def get_chain_stats(self) -> Dict:
        """Get blockchain statistics"""
        total_transactions = sum(len(block.transactions) for block in self.chain)
        total_supply = sum(self.balances.values())
        
        return {
            'total_blocks': len(self.chain),
            'total_transactions': total_transactions,
            'total_supply': total_supply,
            'current_difficulty': self.difficulty,
            'pending_transactions': len(self.pending_transactions),
            'latest_block_hash': self.get_latest_block().block_hash,
            'chain_valid': self.validate_chain()
        }
    
    def export_chain(self) -> str:
        """Export blockchain to JSON"""
        chain_data = {
            'chain': [block.to_dict() for block in self.chain],
            'balances': self.balances,
            'difficulty': self.difficulty,
            'block_reward': self.block_reward
        }
        return json.dumps(chain_data, indent=2)
    
    def import_chain(self, chain_json: str) -> bool:
        """Import blockchain from JSON"""
        try:
            data = json.loads(chain_json)
            
            # Reconstruct chain
            new_chain = [Block.from_dict(block_data) for block_data in data['chain']]
            
            # Validate and replace
            if self.replace_chain(new_chain):
                self.difficulty = data.get('difficulty', 4)
                self.block_reward = data.get('block_reward', 10.0)
                return True
            
            return False
        except Exception:
            return False