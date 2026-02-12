"""
Helper utilities module.
"""
from datetime import datetime, timezone
from typing import Dict, Any
import json

def normalize_timestamp(timestamp_ms: int) -> datetime:
    """Convert millisecond timestamp to UTC datetime."""
    return datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)

def round_to_minute(dt: datetime) -> datetime:
    """Round datetime to nearest minute boundary."""
    return dt.replace(second=0, microsecond=0)

def format_trade_log(trade_data: Dict[str, Any]) -> str:
    """Format trade data for logging."""
    return json.dumps({
        'timestamp': trade_data['timestamp'].isoformat(),
        'symbol': trade_data['symbol'],
        'side': trade_data['side'],
        'quantity': trade_data['quantity'],
        'price': trade_data['price'],
        'variant': trade_data['variant']
    })

def calculate_sl_price(entry_price: float, sl_percent: float, is_long: bool) -> float:
    """Calculate stop loss price based on entry price and percentage."""
    if is_long:
        return entry_price * (1 - sl_percent / 100)
    else:
        return entry_price * (1 + sl_percent / 100)