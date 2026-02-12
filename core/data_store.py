"""
In-memory data store module.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import threading
from utils.logger import setup_logger

logger = setup_logger(__name__)

class TickStore:
    """Store and manage latest tick data per symbol."""
    
    def __init__(self):
        self._latest_ticks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def update_tick(self, symbol: str, price: float, timestamp: datetime, 
                    quantity: float = 0.0) -> None:
        """Update latest tick for symbol."""
        with self._lock:
            self._latest_ticks[symbol] = {
                'symbol': symbol,
                'price': price,
                'quantity': quantity,
                'timestamp': timestamp,
                'received_at': datetime.now(timezone.utc)
            }
    
    def get_latest_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest tick for symbol."""
        with self._lock:
            return self._latest_ticks.get(symbol)
    
    def get_all_ticks(self) -> Dict[str, Dict[str, Any]]:
        """Get all latest ticks."""
        with self._lock:
            return self._latest_ticks.copy()


class CandleStore:
    """Store and manage OHLC candles per symbol."""
    
    def __init__(self, max_candles_per_symbol: int = 100):
        self._candles: Dict[str, List[Dict[str, Any]]] = {}
        self._max_candles = max_candles_per_symbol
        self._lock = threading.Lock()
    
    def add_candle(self, symbol: str, candle: Dict[str, Any]) -> None:
        """Add finalized candle to store."""
        with self._lock:
            if symbol not in self._candles:
                self._candles[symbol] = []
            
            self._candles[symbol].append(candle)
            
            # Maintain max history
            if len(self._candles[symbol]) > self._max_candles:
                self._candles[symbol].pop(0)
    
    def get_candles(self, symbol: str, limit: int = None) -> List[Dict[str, Any]]:
        """Get candles for symbol."""
        with self._lock:
            if symbol not in self._candles:
                return []
            
            candles = self._candles[symbol]
            if limit:
                return candles[-limit:]
            return candles.copy()
    
    def get_latest_candle(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest finalized candle for symbol."""
        with self._lock:
            candles = self._candles.get(symbol, [])
            return candles[-1] if candles else None
    
    def get_all_candles(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all candles."""
        with self._lock:
            return {k: v.copy() for k, v in self._candles.items()}


class PositionStore:
    """Store and manage trading positions per variant."""
    
    def __init__(self):
        self._positions: Dict[str, Dict[str, Any]] = {}
        self._trade_log: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
    
    def open_position(self, variant: str, symbol: str, side: str, 
                      entry_price: float, quantity: float, 
                      sl_price: float) -> None:
        """Open a new position."""
        with self._lock:
            position_id = f"{variant}_{symbol}_{datetime.now().timestamp()}"
            self._positions[position_id] = {
                'id': position_id,
                'variant': variant,
                'symbol': symbol,
                'side': side,
                'entry_price': entry_price,
                'current_price': entry_price,
                'quantity': quantity,
                'sl_price': sl_price,
                'open_time': datetime.now(timezone.utc),
                'close_time': None,
                'status': 'OPEN'
            }
    
    def update_position_pnl(self, position_id: str, current_price: float) -> None:
        """Update position P&L."""
        with self._lock:
            if position_id in self._positions:
                pos = self._positions[position_id]
                pos['current_price'] = current_price
                
                if pos['side'] == 'BUY':
                    pos['pnl_percent'] = ((current_price - pos['entry_price']) 
                                         / pos['entry_price'] * 100)
                else:
                    pos['pnl_percent'] = ((pos['entry_price'] - current_price) 
                                         / pos['entry_price'] * 100)
    
    def close_position(self, position_id: str, close_price: float) -> None:
        """Close an existing position."""
        with self._lock:
            if position_id in self._positions:
                pos = self._positions[position_id]
                pos['close_price'] = close_price
                pos['close_time'] = datetime.now(timezone.utc)
                pos['status'] = 'CLOSED'
                
                # Calculate final P&L
                if pos['side'] == 'BUY':
                    pos['final_pnl'] = (close_price - pos['entry_price']) * pos['quantity']
                else:
                    pos['final_pnl'] = (pos['entry_price'] - close_price) * pos['quantity']
    
    def get_active_positions(self, variant: str = None) -> List[Dict[str, Any]]:
        """Get all active positions."""
        with self._lock:
            positions = []
            for pos in self._positions.values():
                if pos['status'] == 'OPEN':
                    if variant is None or pos['variant'] == variant:
                        positions.append(pos.copy())
            return positions
    
    def add_trade_log(self, trade_data: Dict[str, Any]) -> None:
        """Add trade to log."""
        with self._lock:
            self._trade_log.append(trade_data)
    
    def get_trade_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent trade log."""
        with self._lock:
            return self._trade_log[-limit:]