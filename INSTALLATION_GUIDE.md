# QXChain Installation Guide

## Quick Fix for "ModuleNotFoundError: No module named 'uvicorn'"

You need to install the Python dependencies first. Here are several ways to do it:

## Method 1: Using pip (Recommended)

```bash
cd QXChain
pip install -r requirements.txt
```

## Method 2: Install Individual Packages

If the requirements.txt doesn't work, install the core packages manually:

```bash
pip install fastapi uvicorn websockets requests pydantic
pip install cryptography ecdsa base58 numpy scipy
pip install aiohttp aiosqlite python-multipart
pip install jinja2 structlog rich
```

## Method 3: Using Python Installer Script

```bash
cd QXChain
python install_dependencies.py
```

## Method 4: Using conda (if you have Anaconda/Miniconda)

```bash
conda install fastapi uvicorn websockets requests pydantic
conda install cryptography numpy scipy
pip install ecdsa base58 aiohttp aiosqlite python-multipart jinja2 structlog rich
```

## Verify Installation

After installing, verify it worked:

```bash
python -c "import fastapi, uvicorn; print('Dependencies installed successfully!')"
```

## Run QXChain

Once dependencies are installed:

```bash
# Single node
python node.py --api-port 8000

# Multi-node network
python scripts/run_multi_node.py

# Initialize blockchain first (optional)
python scripts/init_blockchain.py
```

## Troubleshooting

### If pip is not found:
- Make sure Python is properly installed
- Try `python -m pip install -r requirements.txt`
- On some systems, use `pip3` instead of `pip`

### If you get permission errors:
```bash
pip install --user -r requirements.txt
```

### If you get version conflicts:
```bash
pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

### For Windows users:
- Make sure Python is added to PATH
- Try running Command Prompt as Administrator
- Use `py -m pip install -r requirements.txt`

## Minimum Requirements

- Python 3.8 or higher
- pip (Python package installer)
- At least 1GB RAM
- 100MB free disk space

## Quick Start After Installation

1. **Install dependencies** (one of the methods above)
2. **Initialize blockchain**: `python scripts/init_blockchain.py`
3. **Start node**: `python node.py --api-port 8000`
4. **Open dashboard**: http://localhost:8000/dashboard
5. **Test connection**: `python test_dashboard.py`