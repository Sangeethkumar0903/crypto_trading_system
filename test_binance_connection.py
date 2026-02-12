"""
Test Binance Testnet connection.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.binance_client import BinanceStreamClient, BinanceRestClient
from utils.logger import setup_logger, safe_print

logger = setup_logger(__name__)

async def tick_handler(symbol, price, timestamp, quantity):
    """Simple tick handler for testing."""
    safe_print(f"[PRICE] {symbol}: ${price:.2f} @ {timestamp}")

async def test_binance():
    """Test Binance Testnet connection."""
    safe_print("\n" + "="*50)
    safe_print("Testing Binance Testnet Connection")
    safe_print("="*50 + "\n")
    
    # Test 1: REST API
    safe_print("1. Testing REST API...")
    rest_client = BinanceRestClient()
    connection_ok = await rest_client.test_connection()
    
    if connection_ok:
        safe_print("[OK] REST API connection successful")
    else:
        safe_print("[ERROR] REST API connection failed")
        safe_print("   Check your API keys in .env file")
    
    # Test 2: Data streaming
    safe_print("\n2. Testing data streaming (REST polling)...")
    safe_print("   Starting 10-second data stream test...")
    
    stream_client = BinanceStreamClient(tick_handler)
    
    try:
        stream_task = asyncio.create_task(stream_client.start())
        await asyncio.sleep(10)
        stream_client.stop()
        await stream_task
        safe_print("[OK] Data stream test completed")
    except Exception as e:
        safe_print(f"[ERROR] Data stream test failed: {e}")
    
    safe_print("\n" + "="*50)
    safe_print("Test complete")
    safe_print("="*50)

async def test_connection(self) -> bool:
    """Test the connection to Binance Testnet."""
    try:
        if self.client:
            # Just ping the server, don't get account info
            ping = self.client.ping()
            server_time = self.client.get_server_time()
            logger.info(f"Binance Testnet connection successful")
            return True
    except Exception as e:
        logger.error(f"Binance Testnet connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_binance())