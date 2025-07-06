#!/usr/bin/env python3
"""
QXChain Multi-Node Network Launcher
Starts multiple nodes for testing and development
"""

import subprocess
import time
import sys
import os
import signal
import atexit

def main():
    """Launch multiple QXChain nodes"""
    print("🚀 Starting QXChain Multi-Node Network...")
    
    # Node configurations
    nodes = [
        {"port": 5000, "api_port": 8000, "name": "Bootstrap Node"},
        {"port": 5001, "api_port": 8001, "name": "Node 2", "peers": "localhost:8000"},
        {"port": 5002, "api_port": 8002, "name": "Node 3", "peers": "localhost:8000,localhost:8001"}
    ]
    
    processes = []
    
    def cleanup():
        """Clean up processes on exit"""
        print("\n🛑 Shutting down nodes...")
        for proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                proc.kill()
        print("✅ All nodes stopped")
    
    # Register cleanup function
    atexit.register(cleanup)
    
    # Start nodes
    for i, node in enumerate(nodes):
        print(f"🔄 Starting {node['name']} on port {node['api_port']}...")
        
        cmd = [
            sys.executable, "node.py",
            "--host", "localhost",
            "--port", str(node["port"]),
            "--api-port", str(node["api_port"]),
            "--log-level", "INFO"
        ]
        
        # Add peers for non-bootstrap nodes
        if "peers" in node:
            cmd.extend(["--peers", node["peers"]])
        
        try:
            proc = subprocess.Popen(cmd, cwd=os.path.dirname(os.path.abspath(__file__)) + "/..")
            processes.append(proc)
            print(f"✅ {node['name']} started (PID: {proc.pid})")
            
            # Wait a bit between node starts
            if i < len(nodes) - 1:
                time.sleep(3)
        
        except Exception as e:
            print(f"❌ Failed to start {node['name']}: {e}")
            cleanup()
            return
    
    print("\n🎉 All nodes started successfully!")
    print("\n📊 Node Status:")
    for i, node in enumerate(nodes):
        print(f"   {node['name']}: http://localhost:{node['api_port']}")
    
    print("\n🌐 Dashboard URLs:")
    for node in nodes:
        print(f"   http://localhost:{node['api_port']}/dashboard")
    
    print("\n📡 API Endpoints:")
    for node in nodes:
        print(f"   http://localhost:{node['api_port']}/api")
    
    print("\n🔧 Useful Commands:")
    print("   Test network: python scripts/test_network.py")
    print("   Create wallet: curl -X POST http://localhost:8000/api/wallets -H 'Content-Type: application/json' -d '{\"user_id\":\"alice\"}'")
    print("   Start mining: curl -X POST http://localhost:8000/node/mining/start -H 'Content-Type: application/json' -d '{\"miner_address\":\"your_address\"}'")
    
    try:
        print("\n⏳ Network running... Press Ctrl+C to stop all nodes")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Received shutdown signal...")
        cleanup()

if __name__ == "__main__":
    main()