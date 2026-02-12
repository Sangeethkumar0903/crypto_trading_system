"""
Binance WebSocket and REST client module.
"""



import asyncio
import json
import websockets
from typing import List, Callable, Dict, Any, Optional
from datetime import datetime, timezone
from binance.client import Client
from binance.exceptions import BinanceAPIException
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import settings
from utils.logger import setup_logger
from utils.helpers import normalize_timestamp

logger = setup_logger(__name__)


class BinanceStreamClient:
    """REST polling client for Binance Testnet market data streaming."""
    
    def __init__(self, tick_callback: Callable):
        self.tick_callback = tick_callback
        self.symbols = settings.ACTIVE_SYMBOLS
        self.is_running = False
        self.rest_client = None
        self.last_successful_fetch = {}
        self.session = None
        
    def create_session_with_retries(self):
        """Create a requests session with retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
        
    async def start(self):
        """Start streaming using REST API polling."""
        self.is_running = True
        
        # Create session with retries
        self.session = self.create_session_with_retries()
        
        # Initialize REST client without timeout parameter
        try:
            if settings.BINANCE_TESTNET_API_KEY and settings.BINANCE_TESTNET_API_SECRET:
                self.rest_client = Client(
                    settings.BINANCE_TESTNET_API_KEY,
                    settings.BINANCE_TESTNET_API_SECRET,
                    testnet=True
                )
                logger.info("REST polling client initialized (authenticated)")
            else:
                # Try without API keys (public endpoints only)
                self.rest_client = Client(testnet=True)
                logger.info("REST polling client initialized (public endpoints only)")
        except Exception as e:
            logger.error(f"Failed to initialize Binance client: {e}")
            return
        
        logger.info("Using REST API polling for market data")
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.is_running:
            try:
                for symbol in self.symbols:
                    try:
                        # Get ticker price with retry logic
                        for retry in range(3):
                            try:
                                ticker = self.rest_client.get_symbol_ticker(symbol=symbol.upper())
                                price = float(ticker['price'])
                                
                                # Get 24hr ticker for volume
                                ticker_24h = self.rest_client.get_ticker(symbol=symbol.upper())
                                volume = float(ticker_24h.get('quoteVolume', 0))
                                
                                timestamp = datetime.now(timezone.utc)
                                
                                # Call callback
                                await self.tick_callback(symbol, price, timestamp, volume)
                                
                                # Record successful fetch
                                self.last_successful_fetch[symbol] = time.time()
                                consecutive_errors = 0
                                break
                                
                            except Exception as e:
                                if retry == 2:  # Last retry
                                    raise e
                                await asyncio.sleep(0.5)
                                continue
                        
                    except Exception as e:
                        logger.error(f"Error fetching {symbol}: {e}")
                        consecutive_errors += 1
                
                # Dynamic polling interval based on success
                if consecutive_errors > max_consecutive_errors:
                    logger.warning("Too many consecutive errors, increasing poll interval")
                    await asyncio.sleep(2)
                    consecutive_errors = 0
                else:
                    await asyncio.sleep(1)  # Normal 1 second interval
                
            except Exception as e:
                logger.error(f"REST polling error: {e}")
                await asyncio.sleep(5)
    
    def stop(self):
        """Stop streaming."""
        self.is_running = False
        if self.session:
            self.session.close()
        logger.info("REST polling stopped")


class BinanceRestClient:
    """REST client for Binance Testnet order placement."""
    
    def __init__(self):
        self.api_key = settings.BINANCE_TESTNET_API_KEY
        self.api_secret = settings.BINANCE_TESTNET_API_SECRET
        self.base_url = settings.BINANCE_TESTNET_REST_URL
        self.client = None
        self.public_client = None
        self.session = None
        
        # Create session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Always create a public client for testing
        try:
            self.public_client = Client(testnet=True)
            logger.info("Binance public client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize public client: {e}")
        
        if self.api_key and self.api_secret:
            try:
                self.client = Client(
                    self.api_key, 
                    self.api_secret,
                    testnet=True
                )
                logger.info("Binance authenticated client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize authenticated client: {e}")
                self.client = None
        else:
            logger.warning("Binance API credentials not set. Order placement disabled.")
    
    async def place_market_order(self, symbol: str, side: str, 
                                 quantity: float) -> Optional[Dict[str, Any]]:
        """Place a market order on Binance Testnet."""
        if not self.client:
            logger.error("Binance authenticated client not initialized")
            return None
        
        try:
            # Validate side
            side_enum = Client.SIDE_BUY if side.upper() == 'BUY' else Client.SIDE_SELL
            
            # Place order
            order = self.client.create_order(
                symbol=symbol.upper(),
                side=side_enum,
                type=Client.ORDER_TYPE_MARKET,
                quantity=quantity
            )
            
            logger.info(f"Order placed: {order['orderId']} - {side} {quantity} {symbol}")
            return {
                'order_id': order['orderId'],
                'symbol': order['symbol'],
                'side': order['side'],
                'quantity': float(order['executedQty']),
                'price': float(order['fills'][0]['price']) if order.get('fills') else 0,
                'status': order['status']
            }
            
        except BinanceAPIException as e:
            logger.error(f"Binance API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    async def test_connection(self) -> bool:
        """Test the connection to Binance Testnet."""
        # Try public client first
        if self.public_client:
            try:
                # Just ping the server
                self.public_client.ping()
                server_time = self.public_client.get_server_time()
                logger.info(f"Binance Testnet connection successful")
                return True
            except Exception as e:
                logger.error(f"Public connection failed: {e}")
        
        # Try authenticated client if public fails
        if self.client:
            try:
                self.client.ping()
                server_time = self.client.get_server_time()
                logger.info(f"Binance Testnet connection successful (authenticated)")
                return True
            except Exception as e:
                logger.error(f"Authenticated connection failed: {e}")
        
        return False
    
    def __del__(self):
        """Cleanup session on deletion."""
        if self.session:
            self.session.close()