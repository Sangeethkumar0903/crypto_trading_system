"""
Strategy variants with different stop loss levels.
"""
from typing import Dict, Any, Optional
from datetime import datetime

from strategies.sma_ema_strategy import SMAEMAStrategy
from utils.logger import setup_logger
from utils.helpers import calculate_sl_price
from config.settings import settings

logger = setup_logger(__name__)


class StrategyVariantA(SMAEMAStrategy):
    """
    Strategy Variant A - Tighter Stop Loss (15%).
    """
    
    def __init__(self):
        super().__init__(name="SMA_EMA_Variant_A")
        self.stop_loss_percent = settings.SL_VARIANT_A
        logger.info(f"Initialized Variant A with SL: {self.stop_loss_percent}%")
    
    def get_stop_loss_price(self, entry_price: float, side: str) -> float:
        """Calculate stop loss price based on entry and side."""
        is_long = side == 'BUY'
        return calculate_sl_price(entry_price, self.stop_loss_percent, is_long)


class StrategyVariantB(SMAEMAStrategy):
    """
    Strategy Variant B - Looser Stop Loss (10%).
    """
    
    def __init__(self):
        super().__init__(name="SMA_EMA_Variant_B")
        self.stop_loss_percent = settings.SL_VARIANT_B
        logger.info(f"Initialized Variant B with SL: {self.stop_loss_percent}%")
    
    def get_stop_loss_price(self, entry_price: float, side: str) -> float:
        """Calculate stop loss price based on entry and side."""
        is_long = side == 'BUY'
        return calculate_sl_price(entry_price, self.stop_loss_percent, is_long)


class StrategyManager:
    """Manage multiple strategy variants."""
    
    def __init__(self):
        self.variant_a = StrategyVariantA()
        self.variant_b = StrategyVariantB()
        self.active_variants = {
            'A': self.variant_a,
            'B': self.variant_b
        }
    
    def process_candle_all_variants(self, candle: Dict[str, Any], 
                                    candle_history: list[Dict[str, Any]]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Process candle through all strategy variants."""
        signals = {}
        
        for variant_name, strategy in self.active_variants.items():
            signal = strategy.process_candle(candle, candle_history)
            if signal:
                # Add variant info
                signal['variant'] = variant_name
                signal['stop_loss_percent'] = strategy.stop_loss_percent
                signals[variant_name] = signal
        
        return signals
    
    def get_strategy(self, variant: str) -> Optional[SMAEMAStrategy]:
        """Get strategy by variant name."""
        return self.active_variants.get(variant)