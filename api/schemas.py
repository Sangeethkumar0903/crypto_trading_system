"""
Pydantic schemas for API validation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class TickResponse(BaseModel):
    """Tick data response schema."""
    symbol: str
    price: float
    timestamp: datetime
    quantity: Optional[float] = 0


class CandleResponse(BaseModel):
    """Candle data response schema."""
    symbol: str
    open: float
    high: float
    low: float
    close: float
    open_time: datetime
    close_time: datetime
    volume: float
    tick_count: int
    is_finalized: bool


class PositionResponse(BaseModel):
    """Position data response schema."""
    id: str
    variant: str
    symbol: str
    side: str
    entry_price: float
    current_price: float
    quantity: float
    sl_price: float
    pnl_percent: Optional[float] = 0
    status: str
    open_time: datetime
    close_time: Optional[datetime] = None


class TradeLogResponse(BaseModel):
    """Trade log response schema."""
    timestamp: datetime
    symbol: str
    side: str
    quantity: float
    price: float
    variant: str
    order_id: Optional[str] = None


class SignalResponse(BaseModel):
    """Signal response schema."""
    symbol: str
    action: str
    price: float
    timestamp: datetime
    variant: Optional[str] = None
    strength: Optional[str] = None
    reason: Optional[str] = None


class AddSymbolRequest(BaseModel):
    """Request schema for adding symbol."""
    symbol: str = Field(..., pattern="^[a-z0-9]+$")


class SystemStatusResponse(BaseModel):
    """System status response schema."""
    status: str
    active_symbols: List[str]
    active_connections: int
    uptime_seconds: float
    memory_usage: Dict[str, Any]