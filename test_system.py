"""
Simple test script to verify the trading system works.
Run this from the project root directory.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config.settings import settings
    from utils.logger import setup_logger
    from core.data_store import TickStore, CandleStore, PositionStore
    from strategies.sma_ema_strategy import SMAEMAStrategy
except ImportError as e:
    print(f"Import Error: {e}")
    print("\nMake sure you are running this from the project root directory:")
    print("D:\\crypto_trading_system> python test_system.py")
    print("\nAnd that all __init__.py files exist in the subdirectories.")
    sys.exit(1)

logger = setup_logger(__name__)

async def test_components():
    """Test all components are working."""
    print("\n" + "=" * 50)
    print("Testing Crypto Trading System Components")
    print("=" * 50 + "\n")
    
    # Test 1: Settings
    print("✓ Settings loaded successfully")
    print(f"  - API Key configured: {'Yes' if settings.BINANCE_TESTNET_API_KEY else 'No'}")
    print(f"  - Default symbols: {settings.DEFAULT_SYMBOLS}")
    print(f"  - SMA Short: {settings.SMA_SHORT_WINDOW}")
    print(f"  - SMA Long: {settings.SMA_LONG_WINDOW}")
    
    # Test 2: Data Stores
    tick_store = TickStore()
    candle_store = CandleStore()
    position_store = PositionStore()
    print("\n✓ Data stores initialized successfully")
    
    # Test 3: Strategy
    strategy = SMAEMAStrategy()
    print("\n✓ SMA/EMA Strategy initialized successfully")
    print(f"  - SMA Short: {strategy.sma_short_window}")
    print(f"  - SMA Long: {strategy.sma_long_window}")
    print(f"  - EMA Span: {strategy.ema_span}")
    
    # Test 4: Check if .env file exists
    env_file = Path('.env')
    if env_file.exists():
        print("\n✓ .env file found")
    else:
        print("\n⚠ .env file not found. Create it from .env.example")
    
    # Test 5: Check logs directory
    logs_dir = Path('logs')
    if logs_dir.exists():
        print("\n✓ logs directory found")
    else:
        print("\n⚠ logs directory not found. Creating it...")
        logs_dir.mkdir(exist_ok=True)
        print("  ✓ logs directory created")
    
    print("\n" + "=" * 50)
    print("✅ All components initialized successfully!")
    print("\nYou can now run the main system with:")
    print("  python main.py")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    asyncio.run(test_components())