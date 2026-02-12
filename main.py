"""
Main application entry point.
Windows-compatible version with better error handling.


"""


import asyncio
import signal
import sys
from typing import Set
from datetime import datetime
import platform
import socket

from config.settings import settings
from core.binance_client import BinanceStreamClient, BinanceRestClient
from core.candle_aggregator import CandleAggregator
from core.data_store import TickStore, CandleStore, PositionStore
from core.websocket_server import CandleWebSocketServer
from strategies.strategy_variants import StrategyManager
from api.rest_api import TradingAPI
from utils.logger import setup_logger
from utils.helpers import format_trade_log

import uvicorn
from fastapi import FastAPI

logger = setup_logger(__name__)


class TradingSystem:
    """Main trading system orchestrator."""
    
    def __init__(self):
        self.is_running = False
        
        # Initialize components
        self.tick_store = TickStore()
        self.candle_store = CandleStore()
        self.position_store = PositionStore()
        self.strategy_manager = StrategyManager()
        
        # Initialize Binance clients
        self.binance_rest = BinanceRestClient()
        
        # Initialize candle aggregator with callback
        self.candle_aggregator = CandleAggregator(
            candle_callback=self.on_candle_finalized
        )
        
        # Initialize WebSocket client with tick callback
        self.ws_client = BinanceStreamClient(
            tick_callback=self.on_tick_received
        )
        
        # Initialize WebSocket server
        self.ws_server = CandleWebSocketServer()
        
        # Initialize API
        self.api = TradingAPI(
            tick_store=self.tick_store,
            candle_store=self.candle_store,
            position_store=self.position_store,
            strategy_manager=self.strategy_manager
        )
        
        # Tasks
        self.tasks: Set[asyncio.Task] = set()
    
    async def on_tick_received(self, symbol: str, price: float, 
                               timestamp, quantity: float):
        """Handle incoming tick from WebSocket."""
        # Store tick
        self.tick_store.update_tick(symbol, price, timestamp, quantity)
        
        # Process for candle aggregation
        candle = self.candle_aggregator.process_tick(symbol, price, timestamp, quantity)
        
        # Check stop loss for active positions
        await self.check_stop_losses(symbol, price)
    
    def on_candle_finalized(self, candle):
        """Handle finalized candle."""
        # Store candle
        self.candle_store.add_candle(candle['symbol'], candle)
        
        # Broadcast via WebSocket
        asyncio.create_task(self.ws_server.broadcast_candle(candle))
        
        # Get candle history for strategy
        history = self.candle_store.get_candles(
            candle['symbol'], 
            limit=max(settings.SMA_LONG_WINDOW, settings.EMA_SPAN) + 5
        )
        
        # Process strategies
        signals = self.strategy_manager.process_candle_all_variants(candle, history)
        
        # Execute signals
        for variant, signal in signals.items():
            if signal:
                asyncio.create_task(self.execute_signal(variant, signal))
    
    async def check_stop_losses(self, symbol: str, current_price: float):
        """Check and trigger stop losses for active positions."""
        for variant in ['A', 'B']:
            positions = self.position_store.get_active_positions(variant)
            
            for position in positions:
                if position['symbol'] != symbol:
                    continue
                
                # Update P&L
                self.position_store.update_position_pnl(position['id'], current_price)
                
                # Check stop loss
                if position['side'] == 'BUY' and current_price <= position['sl_price']:
                    logger.info(f"Stop loss triggered for {position['id']} at {current_price}")
                    await self.close_position(position, current_price, "Stop Loss")
                
                elif position['side'] == 'SELL' and current_price >= position['sl_price']:
                    logger.info(f"Stop loss triggered for {position['id']} at {current_price}")
                    await self.close_position(position, current_price, "Stop Loss")
    
    async def execute_signal(self, variant: str, signal: dict):
        """Execute trading signal."""
        symbol = signal['symbol']
        side = signal['action']
        price = signal['price']
        quantity = settings.TRADE_QUANTITY
        
        # Get strategy for stop loss
        strategy = self.strategy_manager.get_strategy(variant)
        sl_price = strategy.get_stop_loss_price(price, side)
        
        logger.info(f"Executing {variant} signal: {side} {symbol} @ {price} SL: {sl_price}")
        
        # Place order on Binance Testnet
        order = await self.binance_rest.place_market_order(
            symbol=symbol,
            side=side,
            quantity=quantity
        )
        
        if order:
            # Open position in store
            self.position_store.open_position(
                variant=variant,
                symbol=symbol,
                side=side,
                entry_price=price,
                quantity=quantity,
                sl_price=sl_price
            )
            
            # Log trade
            trade_data = {
                'timestamp': signal['timestamp'],
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'variant': variant,
                'order_id': order.get('order_id'),
                'signal_reason': signal.get('reason')
            }
            
            self.position_store.add_trade_log(trade_data)
            logger.info(f"Trade executed: {format_trade_log(trade_data)}")
    
    async def close_position(self, position: dict, close_price: float, reason: str):
        """Close an open position."""
        # Place closing order on Binance
        close_side = 'SELL' if position['side'] == 'BUY' else 'BUY'
        
        order = await self.binance_rest.place_market_order(
            symbol=position['symbol'],
            side=close_side,
            quantity=position['quantity']
        )
        
        if order:
            # Close position in store
            self.position_store.close_position(position['id'], close_price)
            
            # Log trade
            trade_data = {
                'timestamp': datetime.now(),
                'symbol': position['symbol'],
                'side': close_side,
                'quantity': position['quantity'],
                'price': close_price,
                'variant': position['variant'],
                'order_id': order.get('order_id'),
                'signal_reason': reason
            }
            
            self.position_store.add_trade_log(trade_data)
            logger.info(f"Position closed: {format_trade_log(trade_data)}")
    
    async def start(self):
        """Start all system components."""
        self.is_running = True
        
        try:
            # Start WebSocket server with port fallback
            await self.ws_server.start()
            
            # Start WebSocket client
            ws_task = asyncio.create_task(self.ws_client.start())
            self.tasks.add(ws_task)
            ws_task.add_done_callback(self.tasks.discard)
            
            logger.info("Trading system started")
            
            # Keep running
            try:
                while self.is_running:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                await self.stop()
                
        except Exception as e:
            logger.error(f"Error starting system: {e}")
            await self.stop()
    
    async def stop(self):
        """Stop all system components."""
        logger.info("Shutting down trading system...")
        self.is_running = False
        
        # Force finalize candles
        self.candle_aggregator.force_finalize()
        
        # Stop WebSocket client
        self.ws_client.stop()
        
        # Stop WebSocket server
        await self.ws_server.stop()
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        await asyncio.gather(*self.tasks, return_exceptions=True)
        logger.info("Trading system stopped")


async def run_api(api_app: FastAPI):
    """Run FastAPI server."""
    config = uvicorn.Config(
        api_app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    """Main entry point - Windows compatible."""
    # Create trading system
    system = TradingSystem()
    
    # For Windows: Use simpler signal handling
    is_windows = platform.system() == "Windows"
    
    if not is_windows:
        # Setup signal handlers for Unix-like systems
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(system.stop())
            )
    else:
        logger.info("Running on Windows - use Ctrl+C to stop")
    
    # Run trading system and API concurrently
    try:
        await asyncio.gather(
            system.start(),
            run_api(system.api.get_app())
        )
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        await system.stop()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await system.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")