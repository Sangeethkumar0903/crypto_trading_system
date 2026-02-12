"""
OHLC candle aggregation module.
"""
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta, timezone
import threading
from collections import defaultdict

from utils.logger import setup_logger
from utils.helpers import round_to_minute
from config.settings import settings

logger = setup_logger(__name__)


class CandleAggregator:
    """Real-time OHLC candle aggregator."""
    
    def __init__(self, candle_callback=None):
        self.window_minutes = settings.CANDLE_WINDOW_MINUTES
        self.candle_callback = candle_callback
        
        # Current working candles (not yet finalized)
        self._current_candles: Dict[str, Dict[str, Any]] = {}
        
        # Track processed ticks for each minute window
        self._processed_minutes: Dict[str, set] = defaultdict(set)
        
        self._lock = threading.Lock()
    
    def process_tick(self, symbol: str, price: float, 
                     timestamp: datetime, quantity: float = 0) -> Optional[Dict[str, Any]]:
        """Process a tick and update OHLC candle."""
        with self._lock:
            # Round timestamp to minute boundary
            minute_key = round_to_minute(timestamp)
            
            # Check if this minute is already finalized
            if minute_key in self._processed_minutes[symbol]:
                return None
            
            # Initialize candle for this symbol if not exists
            if symbol not in self._current_candles:
                self._current_candles[symbol] = {
                    'symbol': symbol,
                    'open_time': minute_key,
                    'close_time': minute_key + timedelta(minutes=self.window_minutes),
                    'open': price,
                    'high': price,
                    'low': price,
                    'close': price,
                    'volume': quantity,
                    'tick_count': 1,
                    'is_finalized': False
                }
            else:
                candle = self._current_candles[symbol]
                
                # Check if we need to start a new candle
                if minute_key >= candle['close_time']:
                    # Finalize current candle
                    self._finalize_candle(symbol)
                    
                    # Create new candle
                    self._current_candles[symbol] = {
                        'symbol': symbol,
                        'open_time': minute_key,
                        'close_time': minute_key + timedelta(minutes=self.window_minutes),
                        'open': price,
                        'high': price,
                        'low': price,
                        'close': price,
                        'volume': quantity,
                        'tick_count': 1,
                        'is_finalized': False
                    }
                else:
                    # Update existing candle
                    candle['high'] = max(candle['high'], price)
                    candle['low'] = min(candle['low'], price)
                    candle['close'] = price
                    candle['volume'] += quantity
                    candle['tick_count'] += 1
            
            return self._current_candles.get(symbol)
    
    def _finalize_candle(self, symbol: str):
        """Finalize current candle and trigger callback."""
        if symbol not in self._current_candles:
            return
        
        candle = self._current_candles[symbol]
        candle['is_finalized'] = True
        candle['finalized_at'] = datetime.now(timezone.utc)
        
        # Mark this minute as processed
        self._processed_minutes[symbol].add(candle['open_time'])
        
        # Clean up old processed minutes
        if len(self._processed_minutes[symbol]) > settings.MAX_CANDLES_HISTORY:
            oldest = min(self._processed_minutes[symbol])
            self._processed_minutes[symbol].remove(oldest)
        
        logger.info(f"Candle finalized: {symbol} - "
                   f"O:{candle['open']:.2f} H:{candle['high']:.2f} "
                   f"L:{candle['low']:.2f} C:{candle['close']:.2f}")
        
        # Trigger callback
        if self.candle_callback:
            self.candle_callback(candle.copy())
    
    def get_current_candle(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current working candle for symbol."""
        with self._lock:
            return self._current_candles.get(symbol)
    
    def force_finalize(self, symbol: str = None):
        """Force finalize current candles (useful for shutdown)."""
        with self._lock:
            if symbol:
                self._finalize_candle(symbol)
            else:
                for sym in list(self._current_candles.keys()):
                    self._finalize_candle(sym)