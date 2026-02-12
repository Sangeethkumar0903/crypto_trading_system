"""
FastAPI REST API module.
"""
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import time
import psutil
from datetime import datetime, timezone

from api.schemas import *
from core.data_store import TickStore, CandleStore, PositionStore
from strategies.strategy_variants import StrategyManager
from utils.logger import setup_logger
from config.settings import settings

logger = setup_logger(__name__)


class TradingAPI:
    """FastAPI application for trading system."""
    
    def __init__(self, 
                 tick_store: TickStore,
                 candle_store: CandleStore,
                 position_store: PositionStore,
                 strategy_manager: StrategyManager):
        
        self.tick_store = tick_store
        self.candle_store = candle_store
        self.position_store = position_store
        self.strategy_manager = strategy_manager
        self.start_time = time.time()
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Crypto Trading System API",
            description="Real-time crypto trading with Binance Testnet",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self.setup_routes()
    
    def setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/", tags=["Health"])
        async def root():
            return {
                "service": "Crypto Trading System",
                "status": "running",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        @self.app.get("/api/v1/status", response_model=SystemStatusResponse, tags=["System"])
        async def get_system_status():
            """Get system status."""
            uptime = time.time() - self.start_time
            
            # Memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                "status": "healthy",
                "active_symbols": settings.ACTIVE_SYMBOLS,
                "active_connections": 0,  # Would need to track this
                "uptime_seconds": uptime,
                "memory_usage": {
                    "rss_bytes": memory_info.rss,
                    "vms_bytes": memory_info.vms
                }
            }
        
        @self.app.get("/api/v1/ticks", response_model=List[TickResponse], tags=["Market Data"])
        async def get_all_ticks():
            """Get latest ticks for all symbols."""
            ticks = self.tick_store.get_all_ticks()
            return list(ticks.values())
        
        @self.app.get("/api/v1/ticks/{symbol}", response_model=TickResponse, tags=["Market Data"])
        async def get_tick(symbol: str):
            """Get latest tick for specific symbol."""
            tick = self.tick_store.get_latest_tick(symbol.lower())
            if not tick:
                raise HTTPException(status_code=404, detail="Symbol not found")
            return tick
        
        @self.app.get("/api/v1/candles", tags=["Market Data"])
        async def get_all_candles(limit: Optional[int] = 10):
            """Get latest candles for all symbols."""
            all_candles = self.candle_store.get_all_candles()
            result = {}
            for symbol, candles in all_candles.items():
                result[symbol] = candles[-limit:] if limit else candles
            return result
        
        @self.app.get("/api/v1/candles/{symbol}", response_model=List[CandleResponse], tags=["Market Data"])
        async def get_symbol_candles(symbol: str, limit: int = 20):
            """Get candles for specific symbol."""
            candles = self.candle_store.get_candles(symbol.lower(), limit)
            if not candles:
                raise HTTPException(status_code=404, detail="No candles found for symbol")
            return candles
        
        @self.app.get("/api/v1/positions", response_model=List[PositionResponse], tags=["Trading"])
        async def get_positions(variant: Optional[str] = None):
            """Get active positions."""
            positions = self.position_store.get_active_positions(variant)
            return positions
        
        @self.app.get("/api/v1/trades", response_model=List[TradeLogResponse], tags=["Trading"])
        async def get_trades(limit: int = 100):
            """Get recent trade log."""
            trades = self.position_store.get_trade_log(limit)
            return trades
        
        @self.app.get("/api/v1/signals", tags=["Strategy"])
        async def get_signals(variant: Optional[str] = None, limit: int = 20):
            """Get recent trading signals."""
            if variant:
                strategy = self.strategy_manager.get_strategy(variant)
                if not strategy:
                    raise HTTPException(status_code=404, detail="Variant not found")
                signals = strategy.get_recent_signals(limit)
            else:
                signals = []
                for v in ['A', 'B']:
                    strategy = self.strategy_manager.get_strategy(v)
                    signals.extend(strategy.get_recent_signals(limit // 2))
            
            return sorted(signals, key=lambda x: x['timestamp'], reverse=True)[:limit]
        
        @self.app.post("/api/v1/symbols/add", tags=["Configuration"])
        async def add_symbol(request: AddSymbolRequest):
            """Add new symbol to stream."""
            symbol = request.symbol.lower()
            if symbol not in settings.ACTIVE_SYMBOLS:
                settings.ACTIVE_SYMBOLS.append(symbol)
                logger.info(f"Added symbol: {symbol}")
                return {"status": "success", "symbol": symbol, "active_symbols": settings.ACTIVE_SYMBOLS}
            else:
                return {"status": "already_exists", "symbol": symbol}
        
        @self.app.delete("/api/v1/symbols/{symbol}", tags=["Configuration"])
        async def remove_symbol(symbol: str):
            """Remove symbol from stream."""
            symbol = symbol.lower()
            if symbol in settings.ACTIVE_SYMBOLS:
                settings.ACTIVE_SYMBOLS.remove(symbol)
                logger.info(f"Removed symbol: {symbol}")
                return {"status": "success", "symbol": symbol, "active_symbols": settings.ACTIVE_SYMBOLS}
            else:
                raise HTTPException(status_code=404, detail="Symbol not found")
    
    def get_app(self):
        """Get FastAPI application instance."""
        return self.app