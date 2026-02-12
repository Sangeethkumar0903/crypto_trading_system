"""
Configuration settings module.
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    """Application settings."""
    
    # Binance Testnet
    BINANCE_TESTNET_API_KEY = os.getenv('BINANCE_TESTNET_API_KEY', '')
    BINANCE_TESTNET_API_SECRET = os.getenv('BINANCE_TESTNET_API_SECRET', '')
    BINANCE_TESTNET_WS_URL = 'wss://testnet.binance.vision/ws'  # This is correct
    BINANCE_TESTNET_STREAM_URL = 'wss://testnet.binance.vision/stream'  # Alternative stream URL
    BINANCE_TESTNET_REST_URL = 'https://testnet.binance.vision/api'
    
    # Trading
    TRADE_QUANTITY = float(os.getenv('TRADE_QUANTITY', '0.001'))
    MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', '0.01'))
    
    # Strategy
    SMA_SHORT_WINDOW = int(os.getenv('SMA_SHORT_WINDOW', '5'))
    SMA_LONG_WINDOW = int(os.getenv('SMA_LONG_WINDOW', '20'))
    EMA_SPAN = int(os.getenv('EMA_SPAN', '12'))
    
    # Stop Loss Variants
    SL_VARIANT_A = 15.0  # Tighter SL (15%)
    SL_VARIANT_B = 10.0  # Looser SL (10%)
    
    # Server
    WS_HOST = os.getenv('WS_HOST', 'localhost')
    WS_PORT = int(os.getenv('WS_PORT', '8765'))
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '8000'))
    
    # Symbols
    DEFAULT_SYMBOLS = ['btcusdt', 'ethusdt']
    ACTIVE_SYMBOLS = DEFAULT_SYMBOLS.copy()
    
    # Candle
    CANDLE_WINDOW_MINUTES = 1
    MAX_CANDLES_HISTORY = 100
    
settings = Settings()