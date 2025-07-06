#!/usr/bin/env python3
"""
QXChain Demo Script
Demonstrates the full functionality of the quantum-resistant blockchain
"""

import asyncio
import aiohttp
import json
import time
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def run_demo():
    """Run QXChain demonstration"""
    print("🎭 QXChain Quantum-Resistant Blockchain Demo")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Check if node is running
    print("🔍 Checking if QXChain node is running...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    health = await response.json()
                    print(f"✅ Node is healthy: {health['node_id']}")
                else:
                    print("❌ Node health check failed")
                    return
    except Exception as e:
        print(f"❌ Cannot connect to node: {e}")
        print("💡 Make sure to start a node first: python node.py --api-port 8000")
        return
    
    print("\n" + "=" * 60)
    print("📊 BLOCKCHAIN STATISTICS")
    print("=" * 60)
    
    # Get initial blockchain stats
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{base_url}/api/chain/stats") as response:
            stats = await response.json()
            print(f"📦 Total Blocks: {stats['total_blocks']}")
            print(f"💸 Total Transactions: {stats['total_transactions']}")
            print(f"💰 Total Supply: {stats['total_supply']:.2f} QXC")
            print(f"⚡ Current Difficulty: {stats['current_difficulty']}")
            print(f"⏳ Pending Transactions: {stats['pending_transactions']}")
    
    print("\n" + "=" * 60)
    print("👛 WALLET CREATION")
    print("=" * 60)
    
    # Create Alice's wallet
    print("🔐 Creating Alice's quantum-resistant wallet...")
    async with aiohttp.ClientSession() as session:
        wallet_data = {"user_id": "alice", "password": "alice_secure_pass"}
        async with session.post(f"{base_url}/api/wallets", json=wallet_data) as response:
            alice_wallet = await response.json()
            alice_address = alice_wallet['address']
            print(f"✅ Alice's Address: {alice_address}")
    
    # Create Bob's wallet
    print("🔐 Creating Bob's quantum-resistant wallet...")
    async with aiohttp.ClientSession() as session:
        wallet_data = {"user_id": "bob", "password": "bob_secure_pass"}
        async with session.post(f"{base_url}/api/wallets", json=wallet_data) as response:
            bob_wallet = await response.json()
            bob_address = bob_wallet['address']
            print(f"✅ Bob's Address: {bob_address}")
    
    # Create Miner's wallet
    print("⛏️  Creating Miner's quantum-resistant wallet...")
    async with aiohttp.ClientSession() as session:
        wallet_data = {"user_id": "miner", "password": "miner_secure_pass"}
        async with session.post(f"{base_url}/api/wallets", json=wallet_data) as response:
            miner_wallet = await response.json()
            miner_address = miner_wallet['address']
            print(f"✅ Miner's Address: {miner_address}")
    
    print("\n" + "=" * 60)
    print("💰 INITIAL BALANCES")
    print("=" * 60)
    
    # Check initial balances
    for name, address in [("Alice", alice_address), ("Bob", bob_address), ("Miner", miner_address)]:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/api/balance/{address}") as response:
                balance_data = await response.json()
                print(f"💳 {name}: {balance_data['balance']:.2f} QXC")
    
    print("\n" + "=" * 60)
    print("💸 TRANSACTION CREATION")
    print("=" * 60)
    
    # Create transaction from Alice to Bob
    print("📝 Creating transaction: Alice → Bob (50 QXC)...")
    async with aiohttp.ClientSession() as session:
        tx_data = {
            "sender_user_id": "alice",
            "recipient_address": bob_address,
            "amount": 50.0,
            "fee": 1.0,
            "data": "Payment from Alice to Bob"
        }
        async with session.post(f"{base_url}/api/transactions", json=tx_data) as response:
            if response.status == 200:
                tx_result = await response.json()
                tx_hash = tx_result['transaction']['transaction_hash']
                print(f"✅ Transaction created: {tx_hash[:16]}...")
            else:
                error = await response.text()
                print(f"❌ Transaction failed: {error}")
    
    # Create another transaction
    print("📝 Creating transaction: Alice → Miner (25 QXC)...")
    async with aiohttp.ClientSession() as session:
        tx_data = {
            "sender_user_id": "alice",
            "recipient_address": miner_address,
            "amount": 25.0,
            "fee": 0.5,
            "data": "Payment from Alice to Miner"
        }
        async with session.post(f"{base_url}/api/transactions", json=tx_data) as response:
            if response.status == 200:
                tx_result = await response.json()
                tx_hash = tx_result['transaction']['transaction_hash']
                print(f"✅ Transaction created: {tx_hash[:16]}...")
            else:
                error = await response.text()
                print(f"❌ Transaction failed: {error}")
    
    print("\n" + "=" * 60)
    print("⛏️  MINING DEMONSTRATION")
    print("=" * 60)
    
    # Check pending transactions
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{base_url}/api/transactions/pending") as response:
            pending = await response.json()
            print(f"⏳ Pending transactions: {pending['count']}")
    
    # Start mining
    print("🔨 Starting mining process...")
    async with aiohttp.ClientSession() as session:
        mining_data = {"miner_address": miner_address}
        async with session.post(f"{base_url}/node/mining/start", json=mining_data) as response:
            if response.status == 200:
                print("✅ Mining started")
            else:
                print("❌ Failed to start mining")
    
    # Wait for mining
    print("⏳ Waiting for block to be mined...")
    await asyncio.sleep(10)
    
    # Stop mining
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{base_url}/node/mining/stop") as response:
            if response.status == 200:
                print("🛑 Mining stopped")
    
    print("\n" + "=" * 60)
    print("📊 FINAL STATISTICS")
    print("=" * 60)
    
    # Get final blockchain stats
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{base_url}/api/chain/stats") as response:
            stats = await response.json()
            print(f"📦 Total Blocks: {stats['total_blocks']}")
            print(f"💸 Total Transactions: {stats['total_transactions']}")
            print(f"⏳ Pending Transactions: {stats['pending_transactions']}")
    
    # Check final balances
    print("\n💰 Final Balances:")
    for name, address in [("Alice", alice_address), ("Bob", bob_address), ("Miner", miner_address)]:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/api/balance/{address}") as response:
                balance_data = await response.json()
                print(f"💳 {name}: {balance_data['balance']:.2f} QXC")
    
    print("\n" + "=" * 60)
    print("🎉 DEMO COMPLETE!")
    print("=" * 60)
    print("🌐 View the dashboard at: http://localhost:8000/dashboard")
    print("📡 API documentation: http://localhost:8000/docs")
    print("🔍 Explore the blockchain and verify quantum-resistant signatures!")

def main():
    """Main entry point"""
    print("QXChain Quantum-Resistant Blockchain Demo")
    print("Make sure you have a node running on port 8000:")
    print("  python node.py --api-port 8000")
    print()
    
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n❌ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")

if __name__ == "__main__":
    main()