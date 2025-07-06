#!/usr/bin/env python3
"""
QXChain Dependency Installer
Installs all required Python packages for QXChain
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a Python package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Install all QXChain dependencies"""
    print("🚀 Installing QXChain Dependencies...")
    print("=" * 50)
    
    # Core dependencies
    dependencies = [
        "fastapi==0.104.1",
        "uvicorn==0.24.0", 
        "websockets==12.0",
        "requests==2.31.0",
        "pydantic==2.5.0",
        "cryptography==41.0.7",
        "ecdsa==0.18.0",
        "base58==2.1.1",
        "numpy==1.24.3",
        "scipy==1.11.4",
        "aiosqlite==0.19.0",
        "aiohttp==3.9.1",
        "python-multipart==0.0.6",
        "pytest==7.4.3",
        "pytest-asyncio==0.21.1",
        "jinja2==3.1.2",
        "python-jose==3.3.0",
        "passlib==1.7.4",
        "structlog==23.2.0",
        "rich==13.7.0",
        "flask==3.0.0",
        "flask-cors==4.0.0"
    ]
    
    failed_packages = []
    
    for package in dependencies:
        print(f"📦 Installing {package}...")
        if install_package(package):
            print(f"✅ {package} installed successfully")
        else:
            print(f"❌ Failed to install {package}")
            failed_packages.append(package)
    
    print("\n" + "=" * 50)
    
    if failed_packages:
        print("❌ Some packages failed to install:")
        for package in failed_packages:
            print(f"   - {package}")
        print("\n💡 Try installing manually:")
        print("   pip install " + " ".join(failed_packages))
    else:
        print("🎉 All dependencies installed successfully!")
        print("\n🚀 You can now run QXChain:")
        print("   python node.py --api-port 8000")
        print("   python scripts/run_multi_node.py")
    
    print("\n📋 Verify installation:")
    print("   python -c \"import fastapi, uvicorn; print('QXChain dependencies OK!')\"")

if __name__ == "__main__":
    main()