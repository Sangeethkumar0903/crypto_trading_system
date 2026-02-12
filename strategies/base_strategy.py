"""
Base strategy module.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

from utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseStrategy(ABC):
    """Base class for all trading strategies."""
    
    def __init__(self, name: str):
        self.name = name
        self.signals: List[Dict[str, Any]] = []
    
    @abstractmethod
    def calculate_indicators(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate technical indicators from candle data."""
        pass
    
    @abstractmethod
    def generate_signal(self, symbol: str, 
                        indicators: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate trading signal based on indicators."""
        pass
    
    def process_candle(self, candle: Dict[str, Any], 
                       candle_history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Process a new candle and generate signal if applicable."""
        if not candle_history:
            return None
        
        # Calculate indicators
        indicators = self.calculate_indicators(candle_history)
        
        # Generate signal
        signal = self.generate_signal(candle['symbol'], indicators)
        
        if signal:
            signal['timestamp'] = datetime.now()
            signal['candle_time'] = candle['open_time']
            self.signals.append(signal)
            logger.info(f"Signal generated: {signal}")
            return signal
        
        return None
    
    def get_recent_signals(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent signals."""
        return self.signals[-limit:]