# QXChain Quick Start Guide

## Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize Blockchain**
   ```bash
   python scripts/init_blockchain.py
   ```

## Running QXChain

### Single Node

Start a single node:
```bash
python node.py --api-port 8000
```

Access the dashboard: http://localhost:8000/dashboard

### Multi-Node Network

Start a 3-node network:
```bash
python scripts/run_multi_node.py
```

This starts:
- Node 1: http://localhost:8000
- Node 2: http://localhost:8001  
- Node 3: http://localhost:8002

### Demo

Run the full demonstration:
```bash
python scripts/demo.py
```

## Basic Operations

### Create a Wallet

```bash
curl -X POST http://localhost:8000/api/wallets \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "password": "secure_pass"}'
```

### Check Balance

```bash
curl http://localhost:8000/api/balance/QX_ADDRESS_HERE
```

### Send Transaction

```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "sender_user_id": "alice",
    "recipient_address": "QX_RECIPIENT_ADDRESS",
    "amount": 10.0,
    "fee": 0.1
  }'
```

### Start Mining

```bash
curl -X POST http://localhost:8000/node/mining/start \
  -H "Content-Type: application/json" \
  -d '{"miner_address": "QX_MINER_ADDRESS"}'
```

### Stop Mining

```bash
curl -X POST http://localhost:8000/node/mining/stop
```

## API Endpoints

- `GET /api/chain` - Get full blockchain
- `GET /api/chain/stats` - Get blockchain statistics
- `POST /api/wallets` - Create new wallet
- `GET /api/wallets/{user_id}` - Get wallet info
- `GET /api/balance/{address}` - Get address balance
- `POST /api/transactions` - Create transaction
- `GET /api/transactions/pending` - Get pending transactions
- `POST /api/mine` - Mine a block
- `GET /node/info` - Get node information
- `GET /node/peers` - Get connected peers
- `POST /node/connect` - Connect to peer
- `POST /node/mining/start` - Start mining
- `POST /node/mining/stop` - Stop mining

## Dashboard Features

The web dashboard provides:
- Real-time blockchain statistics
- Network status and peer information
- Wallet management interface
- Transaction creation and monitoring
- Mining controls
- Block explorer
- Live updates via WebSocket

## Testing

Run network tests:
```bash
python scripts/test_network.py
```

## Quantum Resistance

QXChain uses:
- **Kyber1024** for key encapsulation
- **Dilithium-like signatures** for digital signatures
- **SHA3-256** for hashing
- **Post-quantum cryptographic primitives**

All cryptographic operations are designed to be secure against both classical and quantum attacks.

## Troubleshooting

### Node won't start
- Check if port is already in use
- Verify Python dependencies are installed
- Check log output for specific errors

### Transactions failing
- Ensure sender has sufficient balance
- Verify wallet exists and is accessible
- Check transaction signature validity

### Mining not working
- Ensure there are pending transactions
- Check miner address is valid
- Verify node is not already mining

### Peer connection issues
- Check network connectivity
- Verify peer URLs are correct
- Ensure firewall allows connections

## Support

For issues and questions:
- Check the logs for error messages
- Review the API documentation at `/docs`
- Run the demo script to verify functionality
- Test with a single node before multi-node setup