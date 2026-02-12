# crypto_trading_system


![Trading Dashboard](https://img.shields.io/badge/Status-Live-success)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)
![WebSocket](https://img.shields.io/badge/WebSocket-Real--time-orange)
![Binance](https://img.shields.io/badge/Binance-Testnet-yellow)

A professional-grade, real-time cryptocurrency trading system that streams live market data from Binance Testnet, generates 1-minute OHLC candles, runs SMA/EMA strategies with dual risk variants, and executes sample orders. Features a modern, responsive dashboard for real-time monitoring and trading.

---

## 📋 Table of Contents
- [System Overview](#-system-overview)
- [Architecture](#-architecture)
- [Features](#-features)
- [Dashboard Guide](#-dashboard-guide)
- [Technology Stack](#-technology-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the System](#-running-the-system)
- [API Documentation](#-api-documentation)
- [WebSocket Protocol](#-websocket-protocol)
- [Trading Strategies](#-trading-strategies)
- [Project Structure](#-project-structure)
- [Screenshots](#-screenshots)
- [Troubleshooting](#-troubleshooting)
- [Assignment Submission](#-assignment-submission)

---

## 🎯 System Overview

This system is a complete algorithmic trading solution that demonstrates:

✅ **Real-time market data ingestion** from Binance Testnet  
✅ **1-Minute OHLC candle aggregation** from tick data  
✅ **SMA/EMA crossover strategy** with two risk variants  
✅ **Live order execution** on Binance Testnet  
✅ **REST API** for system monitoring and control  
✅ **WebSocket server** for real-time data broadcasting  
✅ **Professional Trading Dashboard** with live charts and metrics  

---

## 🏗 Architecture

┌─────────────────┐ ┌──────────────┐ ┌─────────────────┐
│ Binance │────▶│ Data │────▶│ Candle │
│ Testnet │ │ Ingestion │ │ Aggregator │
└─────────────────┘ └──────────────┘ └─────────────────┘
│ │
▼ ▼
┌─────────────────┐ ┌──────────────┐ ┌─────────────────┐
│ Trading │◀────│ Strategy │◀────│ Candle │
│ Dashboard │ │ Engine │ │ Store │
└─────────────────┘ └──────────────┘ └─────────────────┘
│ │ │
▼ ▼ ▼
┌─────────────────┐ ┌──────────────┐ ┌─────────────────┐
│ WebSocket │ │ REST │ │ Position │
│ Broadcast │ │ API │ │ Manager │
└─────────────────┘ └──────────────┘ └─────────────────┘


---

## ✨ Features

### 🔌 Market Data Ingestion
- **Real-time streaming** via REST polling (WebSocket fallback)
- **Multiple symbols** support (BTCUSDT, ETHUSDT default)
- **Automatic reconnection** with exponential backoff
- **Tick normalization** to UTC timestamps

### 📊 OHLC Aggregation
- **1-Minute candles** generated in real-time
- **No overlap** - candles close exactly on minute boundaries
- **In-memory storage** with configurable history
- **Automatic finalization** of completed candles

### 🤖 Trading Strategies
- **SMA/EMA crossover** logic (SMA 5, SMA 20, EMA 12)
- **Parameterized** lookback windows
- **Signal generation** with strength indicators (STRONG/MODERATE)
- **Real-time** strategy execution on every finalized candle

### ⚖️ Risk Management
| Variant | Stop Loss | Risk Profile | Best For |
|---------|-----------|--------------|----------|
| **Variant A** | 15% | Conservative | Stable markets, lower volatility |
| **Variant B** | 10% | Aggressive | Trending markets, higher volatility |

- **Position tracking** with entry price and current P&L
- **Automatic stop-loss** monitoring and execution
- **Per-variant** state management

### 💼 Order Execution
- **Sample order punching** on Binance Testnet
- **Market orders** with configurable quantities (0.001 default)
- **Secure credential** management via environment variables
- **Comprehensive trade logging** with order IDs

### 🖥️ Professional Dashboard
- **Real-time candlestick charts** with Lightweight Charts
- **Live price feeds** with change indicators
- **Strategy monitoring** cards for both variants
- **Active positions** table with close functionality
- **Trading signals** history with filters
- **Order placement** interface
- **Toast notifications** for system events
- **Fully responsive** design

---




### Dashboard Components

#### 🎯 **KPI Cards**
- **BTC/USDT**: Current Bitcoin price with 24h change percentage
- **ETH/USDT**: Current Ethereum price with 24h change percentage
- **Total P&L**: Realized + unrealized profit/loss (USD and percentage)
- **Active Positions**: Count of currently open positions

#### 📈 **Candlestick Chart**
- **Interactive** - Zoom, pan, and hover for details
- **Professional styling** - Green for bullish, red for bearish
- **Timeframe selection** - 1m, 5m, 15m views
- **Real-time updates** - New candles appear instantly via WebSocket

#### 🃏 **Strategy Cards**
| Feature | Variant A | Variant B |
|---------|-----------|-----------|
| Stop Loss | 15% | 10% |
| Signal Display | BUY/SELL/HOLD | BUY/SELL/HOLD |
| Position Status | LONG/SHORT/NONE | LONG/SHORT/NONE |
| Entry Price | Current position entry | Current position entry |
| P&L | Real-time profit/loss | Real-time profit/loss |
| Color Theme | Blue | Orange |

#### 📋 **Signals Table**
- **Timestamp** - When signal was generated
- **Symbol** - Trading pair
- **Action** - BUY (green) / SELL (red)
- **Price** - Entry price at signal time
- **Variant** - A (blue) / B (orange)
- **Strength** - STRONG (green) / MODERATE (yellow)

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.8+ | Core programming language |
| FastAPI | 0.104.1 | REST API framework |
| WebSockets | 12.0 | Real-time data broadcasting |
| python-binance | 1.0.17 | Binance Testnet integration |
| Uvicorn | 0.24.0 | ASGI server |
| Pydantic | 2.5.0 | Data validation |
| python-dotenv | 1.0.0 | Environment configuration |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| HTML5 | - | Structure |
| CSS3 | - | Styling (Flexbox/Grid) |
| Vanilla JavaScript | ES6 | Interactivity (No frameworks) |
| Lightweight Charts | - | Professional candlestick charts |
| Font Awesome | 6.4.0 | Icons |
| WebSocket API | - | Real-time updates |

### Data Processing
| Technology | Purpose |
|------------|---------|
| asyncio | Asynchronous operations |
| threading | Thread-safe data stores |
| pandas/numpy | Data analysis (optional) |
| logging | Comprehensive logging |

---

## 💻 Installation

### Prerequisites
- ✅ Python 3.8 or higher
- ✅ Git
- ✅ VS Code (recommended)
- ✅ Binance Testnet account (free)

### Step 1: Clone the Repository

git clone https://github.com/yourusername/crypto-trading-system.git
cd crypto-trading-system

### create virtual environment

# Windows
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

### .env:
# Binance Testnet API Credentials (Required for order placement)
BINANCE_TESTNET_API_KEY=your_api_key_here
BINANCE_TESTNET_API_SECRET=your_api_secret_here

# Trading Parameters
TRADE_QUANTITY=0.001        # Order size
MAX_POSITION_SIZE=0.01      # Maximum position per symbol

# Strategy Parameters
SMA_SHORT_WINDOW=5          # Fast SMA period
SMA_LONG_WINDOW=20          # Slow SMA period
EMA_SPAN=12                 # EMA span

# Stop Loss Variants
SL_VARIANT_A=15.0           # Conservative - 15%
SL_VARIANT_B=10.0           # Aggressive - 10%

# Server Settings
WS_HOST=localhost           # WebSocket host
WS_PORT=8765               # WebSocket port (auto-fallback)
API_HOST=0.0.0.0           # API host
API_PORT=8000              # API port



