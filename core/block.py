"""
Block structure for QXChain quantum-resistant blockchain
"""

import hashlib
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from ..crypto.quantum_signatures import QuantumSignature


@dataclass
class Transaction:
    """
    Quantum-resistant transaction structure
    """
    sender: str
    recipient: str
    amount: float
    fee: float
    timestamp: float
    data: Optional[str] = None
    signature: Optional[bytes] = None
    public_key: Optional[bytes] = None
    transaction_hash: Optional[str] = None
    
    def __post_init__(self):
        if self.transaction_hash is None:
            self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate transaction hash"""
        tx_data = {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'fee': self.fee,
            'timestamp': self.timestamp,
            'data': self.data
        }
        tx_string = json.dumps(tx_data, sort_keys=True)
        self.transaction_hash = hashlib.sha3_256(tx_string.encode()).hexdigest()
        return self.transaction_hash
    
    def sign(self, private_key: bytes) -> None:
        """Sign transaction with quantum-resistant signature"""
        message = self.transaction_hash.encode()
        self.signature = QuantumSignature.sign(message, private_key)
    
    def verify_signature(self) -> bool:
        """Verify quantum-resistant signature"""
        if not self.signature or not self.public_key:
            return False
        
        message = self.transaction_hash.encode()
        return QuantumSignature.verify(message, self.signature, self.public_key)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary"""
        return asdict(self)


@dataclass
class Block:
    """
    Quantum-resistant block structure
    """
    index: int
    timestamp: float
    transactions: List[Transaction]
    previous_hash: str
    nonce: int = 0
    difficulty: int = 4
    miner_address: str = ""
    block_reward: float = 10.0
    merkle_root: Optional[str] = None
    block_hash: Optional[str] = None
    
    def __post_init__(self):
        if self.merkle_root is None:
            self.calculate_merkle_root()
        if self.block_hash is None:
            self.calculate_hash()
    
    def calculate_merkle_root(self) -> str:
        """Calculate Merkle root of transactions"""
        if not self.transactions:
            self.merkle_root = hashlib.sha3_256(b'').hexdigest()
            return self.merkle_root
        
        # Get transaction hashes
        tx_hashes = [tx.transaction_hash for tx in self.transactions]
        
        # Build Merkle tree
        while len(tx_hashes) > 1:
            next_level = []
            for i in range(0, len(tx_hashes), 2):
                left = tx_hashes[i]
                right = tx_hashes[i + 1] if i + 1 < len(tx_hashes) else left
                combined = left + right
                next_level.append(hashlib.sha3_256(combined.encode()).hexdigest())
            tx_hashes = next_level
        
        self.merkle_root = tx_hashes[0]
        return self.merkle_root
    
    def calculate_hash(self) -> str:
        """Calculate block hash"""
        block_data = {
            'index': self.index,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'merkle_root': self.merkle_root,
            'nonce': self.nonce,
            'difficulty': self.difficulty,
            'miner_address': self.miner_address
        }
        block_string = json.dumps(block_data, sort_keys=True)
        self.block_hash = hashlib.sha3_256(block_string.encode()).hexdigest()
        return self.block_hash
    
    def mine_block(self, difficulty: Optional[int] = None) -> None:
        """Mine block using proof-of-work"""
        if difficulty is not None:
            self.difficulty = difficulty
        
        target = "0" * self.difficulty
        self.nonce = 0
        
        while not self.block_hash.startswith(target):
            self.nonce += 1
            self.calculate_hash()
    
    def is_valid(self) -> bool:
        """Validate block structure and proof-of-work"""
        # Check hash
        calculated_hash = self.calculate_hash()
        if calculated_hash != self.block_hash:
            return False
        
        # Check proof-of-work
        target = "0" * self.difficulty
        if not self.block_hash.startswith(target):
            return False
        
        # Check Merkle root
        calculated_merkle = self.calculate_merkle_root()
        if calculated_merkle != self.merkle_root:
            return False
        
        # Validate all transactions
        for tx in self.transactions:
            if not tx.verify_signature():
                return False
        
        return True
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """Add transaction to block"""
        if transaction.verify_signature():
            self.transactions.append(transaction)
            self.calculate_merkle_root()
            return True
        return False
    
    def get_total_fees(self) -> float:
        """Calculate total transaction fees in block"""
        return sum(tx.fee for tx in self.transactions)
    
    def get_total_amount(self) -> float:
        """Calculate total transaction amount in block"""
        return sum(tx.amount for tx in self.transactions)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary"""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'difficulty': self.difficulty,
            'miner_address': self.miner_address,
            'block_reward': self.block_reward,
            'merkle_root': self.merkle_root,
            'block_hash': self.block_hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Block':
        """Create block from dictionary"""
        transactions = [Transaction(**tx_data) for tx_data in data.get('transactions', [])]
        
        return cls(
            index=data['index'],
            timestamp=data['timestamp'],
            transactions=transactions,
            previous_hash=data['previous_hash'],
            nonce=data.get('nonce', 0),
            difficulty=data.get('difficulty', 4),
            miner_address=data.get('miner_address', ''),
            block_reward=data.get('block_reward', 10.0),
            merkle_root=data.get('merkle_root'),
            block_hash=data.get('block_hash')
        )
    
    @classmethod
    def create_genesis_block(cls) -> 'Block':
        """Create the genesis block"""
        genesis_tx = Transaction(
            sender="0",
            recipient="genesis",
            amount=42000000.0,  # Total supply
            fee=0.0,
            timestamp=time.time(),
            data="Genesis block - QXChain quantum-resistant blockchain"
        )
        
        return cls(
            index=0,
            timestamp=time.time(),
            transactions=[genesis_tx],
            previous_hash="0",
            difficulty=1,
            miner_address="genesis",
            block_reward=0.0
        )