#!/usr/bin/env python3
"""
Quick test script to verify QXChain dashboard connectivity
"""

import subprocess
import time
import requests
import sys
import os

def test_dashboard_connection():
    """Test dashboard connectivity"""
    print("🧪 Testing QXChain Dashboard Connection...")
    
    # Test if we can reach the API
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is reachable")
            health_data = response.json()
            print(f"   Node ID: {health_data.get('node_id', 'unknown')}")
            print(f"   Status: {health_data.get('status', 'unknown')}")
        else:
            print(f"❌ API server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach API server: {e}")
        print("💡 Make sure to start a node first:")
        print("   python node.py --api-port 8000")
        return False
    
    # Test dashboard endpoint
    try:
        response = requests.get("http://localhost:8000/dashboard", timeout=5)
        if response.status_code == 200:
            print("✅ Dashboard endpoint is working")
            if "QXChain Dashboard" in response.text:
                print("✅ Dashboard HTML is loading correctly")
            else:
                print("⚠️  Dashboard HTML may have issues")
        else:
            print(f"❌ Dashboard endpoint returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Dashboard endpoint error: {e}")
        return False
    
    # Test API endpoints
    api_endpoints = [
        "/api/chain/stats",
        "/api/chain", 
        "/api/transactions/pending"
    ]
    
    print("\n🔍 Testing API endpoints...")
    for endpoint in api_endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint} - OK")
            else:
                print(f"❌ {endpoint} - Status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} - Error: {e}")
    
    # Test WebSocket endpoint (basic check)
    print("\n🔌 WebSocket endpoint should be available at:")
    print("   ws://localhost:8000/ws")
    
    print("\n🌐 Dashboard URLs:")
    print("   Main Dashboard: http://localhost:8000/dashboard")
    print("   API Docs: http://localhost:8000/docs")
    print("   Health Check: http://localhost:8000/health")
    
    return True

def main():
    """Main function"""
    print("QXChain Dashboard Connection Test")
    print("=" * 50)
    
    if test_dashboard_connection():
        print("\n🎉 Dashboard connectivity test PASSED!")
        print("\n📋 Troubleshooting tips if dashboard still shows 'Disconnected':")
        print("   1. Check browser console for JavaScript errors (F12)")
        print("   2. Verify WebSocket connection is not blocked by firewall")
        print("   3. Try refreshing the page (Ctrl+F5)")
        print("   4. Check if running on different port than 8000")
    else:
        print("\n❌ Dashboard connectivity test FAILED!")
        print("\n🔧 To fix the issues:")
        print("   1. Start a QXChain node: python node.py --api-port 8000")
        print("   2. Wait a few seconds for the node to fully start")
        print("   3. Run this test again")

if __name__ == "__main__":
    main()