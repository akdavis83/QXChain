#!/usr/bin/env python3
"""
QXChain Blockchain Initialization Script
Sets up the initial blockchain and creates sample wallets
"""

import sys
import os
import json
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.blockchain import QXBlockchain
from core.block import Transaction

def main():
    """Initialize QXChain blockchain"""
    print("🚀 Initializing QXChain Quantum-Resistant Blockchain...")
    
    # Create blockchain instance
    blockchain = QXBlockchain()
    
    print(f"✅ Genesis block created with hash: {blockchain.get_latest_block().block_hash}")
    
    # Create sample wallets
    print("\n📱 Creating sample wallets...")
    
    # Create Alice's wallet
    alice_wallet = blockchain.create_wallet("alice", "password123")
    print(f"👤 Alice's wallet: {alice_wallet['address']}")
    
    # Create Bob's wallet
    bob_wallet = blockchain.create_wallet("bob", "password456")
    print(f"👤 Bob's wallet: {bob_wallet['address']}")
    
    # Create miner wallet
    miner_wallet = blockchain.create_wallet("miner", "minerpass")
    print(f"⛏️  Miner's wallet: {miner_wallet['address']}")
    
    # Give Alice some initial funds from genesis
    genesis_address = "QX1Genesis1111111111111111111111111"
    
    # Create initial funding transaction
    funding_tx = Transaction(
        sender=genesis_address,
        recipient=alice_wallet['address'],
        amount=1000.0,
        fee=0.0,
        timestamp=time.time(),
        data="Initial funding for Alice"
    )
    
    # Add to pending transactions
    blockchain.pending_transactions.append(funding_tx)
    
    # Mine the first block
    print("\n⛏️  Mining initial block...")
    first_block = blockchain.mine_pending_transactions(miner_wallet['address'])
    print(f"✅ Block {first_block.index} mined with hash: {first_block.block_hash}")
    
    # Update balances manually for genesis transaction
    blockchain.balances[genesis_address] -= 1000.0
    blockchain.balances[alice_wallet['address']] += 1000.0
    
    # Display final state
    print("\n📊 Blockchain Statistics:")
    stats = blockchain.get_chain_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n💰 Wallet Balances:")
    print(f"   Alice ({alice_wallet['address']}): {blockchain.get_balance(alice_wallet['address'])}")
    print(f"   Bob ({bob_wallet['address']}): {blockchain.get_balance(bob_wallet['address'])}")
    print(f"   Miner ({miner_wallet['address']}): {blockchain.get_balance(miner_wallet['address'])}")
    
    # Save blockchain state
    print("\n💾 Saving blockchain state...")
    os.makedirs("data", exist_ok=True)
    
    with open("data/blockchain.json", "w") as f:
        f.write(blockchain.export_chain())
    
    with open("data/wallets.json", "w") as f:
        json.dump(blockchain.wallets, f, indent=2)
    
    print("✅ QXChain initialization complete!")
    print("\n🎯 Next steps:")
    print("   1. Run: python node.py --api-port 8000")
    print("   2. Open: http://localhost:8000/dashboard")
    print("   3. Start mining: POST /node/mining/start with miner address")

if __name__ == "__main__":
    main()