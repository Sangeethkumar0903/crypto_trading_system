"""
SMA/EMA crossover strategy module.
"""
from typing import Dict, Any, List, Optional
import numpy as np

from strategies.base_strategy import BaseStrategy
from utils.logger import setup_logger
from config.settings import settings

logger = setup_logger(__name__)


class SMAEMAStrategy(BaseStrategy):
    """
    SMA/EMA Crossover Strategy.
    
    Generates BUY signal when price crosses above SMA and EMA confirms uptrend.
    Generates SELL signal when price crosses below SMA.
    """
    
    def __init__(self, name: str = "SMA_EMA_Strategy"):
        super().__init__(name)
        self.sma_short_window = settings.SMA_SHORT_WINDOW
        self.sma_long_window = settings.SMA_LONG_WINDOW
        self.ema_span = settings.EMA_SPAN
        
        # Previous values for crossover detection
        self.prev_sma_short = None
        self.prev_sma_long = None
        self.prev_price = None
    
    def calculate_sma(self, prices: List[float], window: int) -> float:
        """Calculate Simple Moving Average."""
        if len(prices) < window:
            return prices[-1] if prices else 0
        return np.mean(prices[-window:])
    
    def calculate_ema(self, prices: List[float], span: int) -> float:
        """Calculate Exponential Moving Average."""
        if len(prices) < 2:
            return prices[-1] if prices else 0
        
        # Simple EMA implementation
        alpha = 2 / (span + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = alpha * price + (1 - alpha) * ema
        return ema
    
    def calculate_indicators(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate SMA and EMA indicators."""
        closes = [c['close'] for c in candles]
        
        indicators = {
            'current_price': closes[-1] if closes else 0,
            'sma_short': self.calculate_sma(closes, self.sma_short_window),
            'sma_long': self.calculate_sma(closes, self.sma_long_window),
            'ema': self.calculate_ema(closes, self.ema_span)
        }
        
        # Store previous values for crossover
        if len(closes) >= 2:
            self.prev_price = closes[-2]
            self.prev_sma_short = self.calculate_sma(closes[:-1], self.sma_short_window)
            self.prev_sma_long = self.calculate_sma(closes[:-1], self.sma_long_window)
        
        return indicators
    
    def generate_signal(self, symbol: str, 
                        indicators: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate trading signal based on SMA/EMA crossover."""
        price = indicators['current_price']
        sma_short = indicators['sma_short']
        sma_long = indicators['sma_long']
        ema = indicators['ema']
        
        # Need enough data for indicators
        if not all([self.prev_sma_short, self.prev_sma_long, self.prev_price]):
            return None
        
        signal = None
        
        # BUY Signal: Price crosses above SMA short and EMA confirms uptrend
        if (self.prev_price <= self.prev_sma_short and 
            price > sma_short and 
            ema > sma_long):
            
            signal = {
                'symbol': symbol,
                'action': 'BUY',
                'price': price,
                'strength': 'STRONG' if price > ema else 'MODERATE',
                'indicators': {
                    'sma_short': sma_short,
                    'sma_long': sma_long,
                    'ema': ema
                },
                'reason': 'Price crossed above SMA with EMA confirmation'
            }
        
        # SELL Signal: Price crosses below SMA short
        elif (self.prev_price >= self.prev_sma_short and 
              price < sma_short):
            
            signal = {
                'symbol': symbol,
                'action': 'SELL',
                'price': price,
                'strength': 'STRONG' if price < ema else 'MODERATE',
                'indicators': {
                    'sma_short': sma_short,
                    'sma_long': sma_long,
                    'ema': ema
                },
                'reason': 'Price crossed below SMA'
            }
        
        return signal