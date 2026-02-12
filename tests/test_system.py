"""
Simple test script to verify the trading system works.
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings
from utils.logger import setup_logger
from core.data_store import TickStore, CandleStore, PositionStore
from strategies.sma_ema_strategy import SMAEMAStrategy

logger = setup_logger(__name__)

async def test_components():
    """Test all components are working."""
    logger.info("=" * 50)
    logger.info("Testing Crypto Trading System Components")
    logger.info("=" * 50)
    
    # Test 1: Settings
    logger.info("✓ Settings loaded successfully")
    logger.info(f"  - API Key configured: {'Yes' if settings.BINANCE_TESTNET_API_KEY else 'No'}")
    logger.info(f"  - Default symbols: {settings.DEFAULT_SYMBOLS}")
    
    # Test 2: Data Stores
    tick_store = TickStore()
    candle_store = CandleStore()
    position_store = PositionStore()
    logger.info("✓ Data stores initialized successfully")
    
    # Test 3: Strategy
    strategy = SMAEMAStrategy()
    logger.info("✓ SMA/EMA Strategy initialized successfully")
    logger.info(f"  - SMA Short: {strategy.sma_short_window}")
    logger.info(f"  - SMA Long: {strategy.sma_long_window}")
    logger.info(f"  - EMA Span: {strategy.ema_span}")
    
    logger.info("\n" + "=" * 50)
    logger.info("All components initialized successfully!")
    logger.info("You can now run the main system with: python main.py")
    logger.info("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_components())