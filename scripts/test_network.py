#!/usr/bin/env python3
"""
QXChain Network Testing Script
Tests multi-node network functionality
"""

import asyncio
import aiohttp
import json
import time
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_network():
    """Test QXChain network functionality"""
    print("🧪 Testing QXChain Network...")
    
    # Node configurations
    nodes = [
        {"host": "localhost", "port": 8000, "name": "Node1"},
        {"host": "localhost", "port": 8001, "name": "Node2"},
        {"host": "localhost", "port": 8002, "name": "Node3"}
    ]
    
    # Test node connectivity
    print("\n🔗 Testing node connectivity...")
    active_nodes = []
    
    for node in nodes:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{node['host']}:{node['port']}/health"
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ {node['name']} is online - {data.get('node_id', 'unknown')}")
                        active_nodes.append(node)
                    else:
                        print(f"❌ {node['name']} returned status {response.status}")
        except Exception as e:
            print(f"❌ {node['name']} is offline: {e}")
    
    if len(active_nodes) < 2:
        print("❌ Need at least 2 nodes running for network tests")
        return
    
    # Test peer connections
    print("\n🤝 Testing peer connections...")
    
    # Connect Node2 to Node1
    try:
        async with aiohttp.ClientSession() as session:
            url = f"http://{active_nodes[1]['host']}:{active_nodes[1]['port']}/node/connect"
            peer_url = f"http://{active_nodes[0]['host']}:{active_nodes[0]['port']}"
            
            async with session.post(url, json={"url": peer_url}) as response:
                if response.status == 200:
                    print(f"✅ {active_nodes[1]['name']} connected to {active_nodes[0]['name']}")
                else:
                    print(f"❌ Failed to connect nodes: {response.status}")
    except Exception as e:
        print(f"❌ Peer connection failed: {e}")
    
    # Test wallet creation
    print("\n👛 Testing wallet creation...")
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"http://{active_nodes[0]['host']}:{active_nodes[0]['port']}/api/wallets"
            wallet_data = {"user_id": "test_user", "password": "test_pass"}
            
            async with session.post(url, json=wallet_data) as response:
                if response.status == 200:
                    wallet = await response.json()
                    print(f"✅ Wallet created: {wallet['address']}")
                    test_address = wallet['address']
                else:
                    print(f"❌ Wallet creation failed: {response.status}")
                    return
    except Exception as e:
        print(f"❌ Wallet creation error: {e}")
        return
    
    # Test transaction creation
    print("\n💸 Testing transaction creation...")
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"http://{active_nodes[0]['host']}:{active_nodes[0]['port']}/api/transactions"
            tx_data = {
                "sender_user_id": "test_user",
                "recipient_address": "QX1Genesis1111111111111111111111111",
                "amount": 10.0,
                "fee": 0.1
            }
            
            async with session.post(url, json=tx_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Transaction created: {result['transaction']['transaction_hash']}")
                else:
                    print(f"❌ Transaction creation failed: {response.status}")
    except Exception as e:
        print(f"❌ Transaction creation error: {e}")
    
    # Test mining
    print("\n⛏️  Testing mining...")
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"http://{active_nodes[0]['host']}:{active_nodes[0]['port']}/node/mining/start"
            mining_data = {"miner_address": test_address}
            
            async with session.post(url, json=mining_data) as response:
                if response.status == 200:
                    print("✅ Mining started")
                    
                    # Wait a bit for mining
                    await asyncio.sleep(5)
                    
                    # Stop mining
                    stop_url = f"http://{active_nodes[0]['host']}:{active_nodes[0]['port']}/node/mining/stop"
                    async with session.post(stop_url) as stop_response:
                        if stop_response.status == 200:
                            print("✅ Mining stopped")
                else:
                    print(f"❌ Mining start failed: {response.status}")
    except Exception as e:
        print(f"❌ Mining test error: {e}")
    
    # Test blockchain stats
    print("\n📊 Testing blockchain statistics...")
    
    for node in active_nodes:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{node['host']}:{node['port']}/api/chain/stats"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        stats = await response.json()
                        print(f"✅ {node['name']} - Blocks: {stats['total_blocks']}, "
                              f"Transactions: {stats['total_transactions']}")
                    else:
                        print(f"❌ {node['name']} stats failed: {response.status}")
        except Exception as e:
            print(f"❌ {node['name']} stats error: {e}")
    
    print("\n🎉 Network testing complete!")

def main():
    """Main entry point"""
    print("QXChain Network Test Suite")
    print("=" * 50)
    print("Make sure you have nodes running on ports 8000, 8001, 8002")
    print("Start nodes with:")
    print("  python node.py --api-port 8000")
    print("  python node.py --api-port 8001")
    print("  python node.py --api-port 8002")
    print("=" * 50)
    
    try:
        asyncio.run(test_network())
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    main()