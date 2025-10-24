# ChainForge - Django Blockchain API

A fully-featured blockchain implementation built with Django and Django REST Framework, featuring dynamic difficulty adjustment, JWT authentication, and comprehensive API endpoints for blockchain operations.

## 🚀 Features

- **Complete Blockchain Implementation**: Genesis block creation, mining, transaction management, and chain validation
- **Dynamic Difficulty Adjustment**: Bitcoin-style automatic difficulty adjustment based on mining performance
- **JWT Authentication**: Secure API access with token-based authentication
- **Rate Limiting**: Redis-based rate limiting to prevent API abuse
- **Comprehensive API**: 20+ endpoints for blockchain operations
- **Admin Controls**: Special endpoints for blockchain management and configuration
- **Real-time Statistics**: Mining performance metrics and blockchain analytics

## 📋 Prerequisites

- Python 3.13+
- Redis Server (for caching and rate limiting)
- Git

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd chainforge
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

**Activate the virtual environment:**

- **Windows**: `venv\Scripts\activate`
- **Mac/Linux**: `source venv/bin/activate`

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install and Start Redis

**Windows (using Chocolatey):**

```bash
choco install redis-64
redis-server
```

**Mac (using Homebrew):**

```bash
brew install redis
brew services start redis
```

**Linux:**

```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

**Verify Redis is running:**

```bash
redis-cli ping
# Should return: PONG
```

### 5. Environment Configuration

Create a `.env` file in the project root:

```env
# Django Core
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True

# Security (Disabled for local development)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_HSTS_SECONDS=0

# Hosts
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS (for frontend development)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

### 6. Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 8. Run the Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

## 🔐 Authentication

### 1. Get Access Token

**Endpoint:** `POST http://localhost:8000/api/blockchain/token/`

**Request Body:**

```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**

```json
{
  "refresh": "your_refresh_token",
  "access": "your_access_token"
}
```

### 2. Use Token in Requests

Add the following header to all subsequent requests:

```
Authorization: Bearer your_access_token
```

### 3. Refresh Token

**Endpoint:** `POST http://localhost:8000/api/blockchain/token/refresh/`

**Request Body:**

```json
{
  "refresh": "your_refresh_token"
}
```

## 📚 Complete API Endpoints Reference

### 🔐 Authentication Endpoints

| Method | Endpoint                         | Description                       | Auth Required | Admin Only |
| ------ | -------------------------------- | --------------------------------- | ------------- | ---------- |
| POST   | `/api/blockchain/token/`         | Get JWT access and refresh tokens | ❌            | ❌         |
| POST   | `/api/blockchain/token/refresh/` | Refresh expired access token      | ❌            | ❌         |

**Example - Get Token:**

```bash
POST /api/blockchain/token/
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}
```

**Response:**

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### ⛓️ Blockchain Core Endpoints

| Method | Endpoint                      | Description                   | Auth Required | Admin Only | Rate Limit |
| ------ | ----------------------------- | ----------------------------- | ------------- | ---------- | ---------- |
| POST   | `/api/blockchain/initialize/` | Create genesis block          | ✅            | ✅         | 2/min      |
| GET    | `/api/blockchain/chain/`      | Get entire blockchain         | ✅            | ❌         | 100/min    |
| GET    | `/api/blockchain/validate/`   | Validate blockchain integrity | ✅            | ❌         | 100/min    |
| GET    | `/api/blockchain/summary/`    | Get blockchain statistics     | ✅            | ❌         | 100/min    |
| POST   | `/api/blockchain/reset/`      | Delete all blockchain data    | ✅            | ✅         | 2/min      |

#### 1. Initialize Blockchain

```bash
POST /api/blockchain/initialize/
Authorization: Bearer {access_token}
```

**Response:**

```json
{
  "message": "Blockchain initialized with genesis block",
  "genesis_block": {
    "index": 0,
    "hash": "000abc123..."
  }
}
```

#### 2. Get Blockchain

```bash
GET /api/blockchain/chain/
Authorization: Bearer {access_token}
```

**Response:**

```json
{
  "chain": [
    {
      "index": 0,
      "timestamp": "2025-10-23T12:00:00Z",
      "data": { "message": "Genesis Block" },
      "previous_hash": "0",
      "hash": "000abc123...",
      "nonce": 12345
    }
  ],
  "length": 1
}
```

#### 3. Validate Chain

```bash
GET /api/blockchain/validate/
Authorization: Bearer {access_token}
```

**Response:**

```json
{
  "valid": true,
  "message": "Blockchain is valid"
}
```

#### 4. Get Blockchain Summary

```bash
GET /api/blockchain/summary/
Authorization: Bearer {access_token}
```

**Response:**

```json
{
    "summary": {
        "total_blocks": 15,
        "total_transactions": 150,
        "pending_transactions": 5,
        "completed_transactions": 145,
        "total_value_transferred": "12500.00",
        "current_difficulty": 4
    },
    "recent_blocks": [...],
    "mining_stats": {...}
}
```

#### 5. Reset Blockchain

```bash
POST /api/blockchain/reset/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "confirm": true
}
```

**Response:**

```json
{
  "message": "Blockchain reset successfully",
  "blocks_deleted": true,
  "transactions_deleted": true,
  "difficulty_reset": 4
}
```

---

### 💰 Transaction Endpoints

| Method | Endpoint                                | Description                  | Auth Required | Admin Only | Rate Limit |
| ------ | --------------------------------------- | ---------------------------- | ------------- | ---------- | ---------- |
| POST   | `/api/blockchain/transaction/create/`   | Create single transaction    | ✅            | ❌         | 50/min     |
| GET    | `/api/blockchain/pending-transactions/` | Get all pending transactions | ✅            | ❌         | 100/min    |
| POST   | `/api/blockchain/batch-transactions/`   | Create multiple transactions | ✅            | ❌         | 50/min     |
| GET    | `/api/blockchain/balance/{address}/`    | Get balance for address      | ✅            | ❌         | 100/min    |

#### 1. Create Transaction

```bash
POST /api/blockchain/transaction/create/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "sender": "Alice",
    "receiver": "Bob",
    "amount": 50.00
}
```

**Response:**

```json
{
  "message": "Transaction created successfully",
  "transaction": {
    "id": 1,
    "sender": "Alice",
    "receiver": "Bob",
    "amount": "50.00"
  }
}
```

#### 2. Get Pending Transactions

```bash
GET /api/blockchain/pending-transactions/
Authorization: Bearer {access_token}
```

**Response:**

```json
{
  "pending_transactions": [
    {
      "id": 1,
      "sender": "Alice",
      "receiver": "Bob",
      "amount": "50.00",
      "timestamp": "2025-10-23T12:30:00Z"
    }
  ]
}
```

#### 3. Batch Create Transactions

```bash
POST /api/blockchain/batch-transactions/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "count": 10
}
```

**Parameters:**

- `count` (integer, 1-1000): Number of random transactions to create

**Response:**

```json
{
  "message": "10 transactions created successfully",
  "transactions_count": 10,
  "sample_transactions": [
    {
      "id": 1,
      "sender": "Alice",
      "receiver": "Bob",
      "amount": "125.50"
    }
  ]
}
```

#### 4. Get Balance

```bash
GET /api/blockchain/balance/Alice/
Authorization: Bearer {access_token}
```

**Response:**

```json
{
  "address": "Alice",
  "balance": "450.00"
}
```

---

### ⛏️ Mining Endpoints

| Method | Endpoint                        | Description                  | Auth Required | Admin Only | Rate Limit |
| ------ | ------------------------------- | ---------------------------- | ------------- | ---------- | ---------- |
| POST   | `/api/blockchain/mine/`         | Mine pending transactions    | ✅            | ❌         | 5/min      |
| POST   | `/api/blockchain/batch-mine/`   | Mine multiple blocks         | ✅            | ❌         | 5/min      |
| GET    | `/api/blockchain/mining-stats/` | Get mining performance stats | ✅            | ❌         | 100/min    |

#### 1. Mine Block

```bash
POST /api/blockchain/mine/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "miner_address": "Miner1"
}
```

**Response:**

```json
{
  "message": "Block mined successfully",
  "block": {
    "index": 5,
    "hash": "0000abc123...",
    "transactions": 10
  },
  "difficulty_adjustment": {
    "adjusted": true,
    "old_difficulty": 4,
    "new_difficulty": 5,
    "reason": "increased (blocks mined too fast)"
  }
}
```

#### 2. Batch Mine Blocks

```bash
POST /api/blockchain/batch-mine/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "count": 5,
    "miner_address": "BatchMiner",
    "auto_adjust": true
}
```

**Parameters:**

- `count` (integer, 1-50): Number of blocks to mine
- `miner_address` (string, optional): Miner identifier (default: "BatchMiner")
- `auto_adjust` (boolean, default: true): Enable automatic difficulty adjustment

**Response:**

```json
{
  "message": "5 blocks mined successfully",
  "blocks_mined": 5,
  "blocks": [
    {
      "index": 6,
      "hash": "0000def456...",
      "nonce": 54321,
      "transactions": 8,
      "difficulty": 4,
      "timestamp": "2025-10-23T13:00:00Z"
    }
  ],
  "difficulty_adjustments": [
    {
      "at_block": 10,
      "adjustment": {
        "old_difficulty": 4,
        "new_difficulty": 5
      }
    }
  ],
  "final_difficulty": 5
}
```

#### 3. Get Mining Statistics

```bash
GET /api/blockchain/mining-stats/
Authorization: Bearer {access_token}
```

**Response:**

```json
{
  "total_blocks": 25,
  "current_difficulty": 4,
  "target_block_time": 10,
  "average_block_time": 9.85,
  "last_10_blocks": [12.3, 8.5, 9.2, 10.1, 8.9, 11.2, 9.5, 10.8, 8.7, 9.4],
  "adjustment_interval": 5,
  "next_adjustment_at_block": 30
}
```

---

### ⚙️ Difficulty Management Endpoints (Admin Only)

| Method | Endpoint                                   | Description                     | Auth Required | Admin Only | Rate Limit |
| ------ | ------------------------------------------ | ------------------------------- | ------------- | ---------- | ---------- |
| GET    | `/api/blockchain/difficulty/`              | Get current difficulty settings | ✅            | ❌         | 100/min    |
| POST   | `/api/blockchain/set-difficulty/`          | Manually set difficulty         | ✅            | ✅         | 2/min      |
| POST   | `/api/blockchain/set-target-time/`         | Set target block time           | ✅            | ✅         | 2/min      |
| POST   | `/api/blockchain/set-adjustment-interval/` | Set adjustment interval         | ✅            | ✅         | 2/min      |
| POST   | `/api/blockchain/adjust-difficulty/`       | Manually trigger adjustment     | ✅            | ✅         | 2/min      |

#### 1. Get Current Difficulty

```bash
GET /api/blockchain/difficulty/
Authorization: Bearer {access_token}
```

**Response:**

```json
{
  "difficulty": 4,
  "target_block_time": 10,
  "adjustment_interval": 5
}
```

#### 2. Set Difficulty

```bash
POST /api/blockchain/set-difficulty/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "difficulty": 5
}
```

**Parameters:**

- `difficulty` (integer, 1-10): New mining difficulty level

**Response:**

```json
{
  "message": "Difficulty set to 5",
  "difficulty": 5
}
```

#### 3. Set Target Block Time

```bash
POST /api/blockchain/set-target-time/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "target_time": 15
}
```

**Parameters:**

- `target_time` (integer, 1-300): Target seconds per block

**Response:**

```json
{
  "message": "Target block time set to 15 seconds",
  "target_block_time": 15
}
```

#### 4. Set Adjustment Interval

```bash
POST /api/blockchain/set-adjustment-interval/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "interval": 10
}
```

**Parameters:**

- `interval` (integer, 1-100): Number of blocks between adjustments

**Response:**

```json
{
  "message": "Adjustment interval set to 10 blocks",
  "adjustment_interval": 10
}
```

#### 5. Manual Difficulty Adjustment

```bash
POST /api/blockchain/adjust-difficulty/
Authorization: Bearer {access_token}
```

**Response:**

```json
{
  "message": "Difficulty increased (blocks mined too fast)",
  "adjustment_info": {
    "adjusted": true,
    "old_difficulty": 4,
    "new_difficulty": 5,
    "reason": "increased (blocks mined too fast)",
    "blocks_analyzed": 5,
    "actual_time": 38.5,
    "expected_time": 50.0,
    "ratio": 0.77
  }
}
```

---

### 🎮 Utility & Simulation Endpoints

| Method | Endpoint                       | Description                   | Auth Required | Admin Only | Rate Limit |
| ------ | ------------------------------ | ----------------------------- | ------------- | ---------- | ---------- |
| POST   | `/api/blockchain/quick-setup/` | Initialize with sample data   | ✅            | ✅         | 2/min      |
| POST   | `/api/blockchain/simulate/`    | Simulate blockchain operation | ✅            | ❌         | 5/min      |

#### 1. Quick Setup

```bash
POST /api/blockchain/quick-setup/
Authorization: Bearer {access_token}
```

**Description:** Automatically initializes blockchain and creates sample transactions and blocks.

**Response:**

```json
{
  "message": "Quick setup complete!",
  "blockchain_initialized": true,
  "blocks_created": 5,
  "blocks": [
    {
      "index": 1,
      "hash": "0000abc123..."
    }
  ],
  "current_difficulty": 4,
  "total_blocks": 6
}
```

#### 2. Simulate Blockchain

```bash
POST /api/blockchain/simulate/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "blocks": 10,
    "transactions_per_block": 5,
    "miner_address": "Simulator"
}
```

**Parameters:**

- `blocks` (integer, 1-100): Number of blocks to create
- `transactions_per_block` (integer, 1-50): Transactions per block
- `miner_address` (string, optional): Miner identifier (default: "Simulator")

**Response:**

```json
{
    "message": "Simulation complete: 10 blocks created",
    "summary": {
        "blocks_mined": 10,
        "total_transactions": 50,
        "difficulty_adjustments": 2,
        "final_difficulty": 5
    },
    "details": {
        "blocks_created": [...],
        "difficulty_changes": [
            {
                "at_block": 5,
                "old_difficulty": 4,
                "new_difficulty": 5,
                "reason": "increased (blocks mined too fast)"
            }
        ],
        "total_transactions": 50
    }
}
```

---

## 📊 Complete Endpoint Summary

**Total Endpoints:** 23

### By Category:

- **Authentication:** 2 endpoints
- **Blockchain Core:** 5 endpoints
- **Transactions:** 4 endpoints
- **Mining:** 3 endpoints
- **Difficulty Management:** 5 endpoints
- **Utilities:** 2 endpoints
- **Quick Setup:** 2 endpoints

### By Method:

- **GET:** 8 endpoints
- **POST:** 15 endpoints

### By Access Level:

- **Public (No Auth):** 2 endpoints
- **Authenticated:** 14 endpoints
- **Admin Only:** 7 endpoints

### Rate Limits:

- **2/min:** Admin configuration endpoints
- **5/min:** Mining operations
- **50/min:** Transaction creation
- **100/min:** Read operations

## 🧪 Testing with Postman

### 1. Import Postman Collection

Create a new Postman collection and add an environment with:

**Variables:**

- `base_url`: `http://localhost:8000/api/blockchain`
- `access_token`: (will be set automatically)

### 2. Auto-Save Token Script

In your token request, add this to the **Tests** tab:

```javascript
if (pm.response.code === 200) {
  var jsonData = pm.response.json();
  pm.environment.set("access_token", jsonData.access);
  pm.environment.set("refresh_token", jsonData.refresh);
}
```

### 3. Use Token in Requests

In other requests:

- **Authorization Type**: Bearer Token
- **Token**: `{{access_token}}`

## 🔧 Configuration

### Blockchain Settings

Edit `blockchain/blockchain.py` to modify:

```python
DIFFICULTY = 4              # Initial mining difficulty (1-10)
MINING_REWARD = 10          # Reward for mining a block
TARGET_BLOCK_TIME = 10      # Target seconds per block
ADJUSTMENT_INTERVAL = 5     # Blocks between difficulty adjustments
```

### Rate Limiting

Edit `blockchain/views.py` to adjust rate limits:

```python
@ratelimit(key='user', rate='100/m', method='GET', block=True)  # 100 requests per minute
@ratelimit(key='user', rate='50/m', method='POST', block=True)  # 50 requests per minute
```

## 📊 Project Structure

```
chainforge/
├── blockchain/              # Main blockchain app
│   ├── models.py           # Block and Transaction models
│   ├── blockchain.py       # Blockchain logic
│   ├── views.py            # API endpoints
│   ├── urls.py             # URL routing
│   └── permissions.py      # Custom permissions
├── chainforge/             # Project settings
│   ├── settings.py         # Django settings
│   ├── urls.py             # Main URL configuration
│   └── wsgi.py             # WSGI configuration
├── db.sqlite3              # SQLite database
├── manage.py               # Django management script
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables
```

## 🐛 Troubleshooting

### Redis Connection Error

**Error:** `Error 10061 connecting to 127.0.0.1:6379`

**Solution:**

1. Make sure Redis is installed and running
2. Verify with: `redis-cli ping`
3. If not installed, follow the Redis installation steps above

**Alternative:** Use dummy cache in `settings.py`:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
```

### HTTPS/SSL Errors

**Error:** `You're accessing the development server over HTTPS`

**Solution:** Use `http://` instead of `https://` in your requests

### 404 Errors

**Issue:** URL not found

**Solution:** Verify the URL structure:

- ✅ `http://localhost:8000/api/blockchain/token/`
- ❌ `http://localhost:8000/token/`

### Authentication Errors

**Error:** `Authentication credentials were not provided`

**Solution:** Add Bearer token to Authorization header

## 🚀 Quick Start Workflow

1. **Start Redis**

   ```bash
   redis-server
   ```

2. **Start Django Server**

   ```bash
   python manage.py runserver
   ```

3. **Get Authentication Token**

   ```bash
   POST http://localhost:8000/api/blockchain/token/
   Body: {"username": "admin", "password": "your_password"}
   ```

4. **Initialize Blockchain**

   ```bash
   POST http://localhost:8000/api/blockchain/initialize/
   Authorization: Bearer your_token
   ```

5. **Create Transactions**

   ```bash
   POST http://localhost:8000/api/blockchain/batch-transactions/
   Body: {"count": 10}
   ```

6. **Mine a Block**

   ```bash
   POST http://localhost:8000/api/blockchain/mine/
   Body: {"miner_address": "Miner1"}
   ```

7. **View the Chain**
   ```bash
   GET http://localhost:8000/api/blockchain/chain/
   ```

## 📝 Key Concepts

### Mining & Proof of Work

ChainForge implements a proof-of-work algorithm where miners must find a hash that meets the current difficulty requirement (number of leading zeros).

### Dynamic Difficulty Adjustment

Like Bitcoin, ChainForge automatically adjusts mining difficulty every N blocks to maintain a target block time.

### Transaction Flow

1. Create transaction → Pending pool
2. Mine block → Transactions added to block
3. Block validated → Transactions confirmed
4. Miner receives reward → New pending transaction

## 🔒 Security Notes

**For Production:**

1. **Change these settings in `.env`:**

   ```env
   DEBUG=False
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   SECURE_HSTS_SECONDS=31536000
   ```

2. **Use a strong secret key**
3. **Use PostgreSQL instead of SQLite**
4. **Set up proper HTTPS with SSL certificates**
5. **Use environment-specific settings**

## 📄 License

This project is open source and available under the MIT License.

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please open an issue on the GitHub repository.

---

**Built with ❤️ using Django, Django REST Framework, and Redis**

ad this in script section of postman:

````if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.environment.set("access_token", jsonData.access);
    pm.environment.set("refresh_token", jsonData.refresh);
}```
````
