"""
Custom WebSocket server for broadcasting candle updates.
"""
import asyncio
import json
import websockets
from typing import Set, Dict, Any
from datetime import datetime
import socket

from utils.logger import setup_logger
from config.settings import settings

logger = setup_logger(__name__)


class CandleWebSocketServer:
    """WebSocket server for broadcasting candle updates to clients."""
    
    def __init__(self):
        self.host = settings.WS_HOST
        self.port = settings.WS_PORT
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
    
    def is_port_available(self, port):
        """Check if a port is available."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((self.host, port))
                return True
            except socket.error:
                return False
    
    async def register(self, websocket: websockets.WebSocketServerProtocol):
        """Register a new client."""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
    
    async def unregister(self, websocket: websockets.WebSocketServerProtocol):
        """Unregister a client."""
        self.clients.remove(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def broadcast_candle(self, candle_data: Dict[str, Any]):
        """Broadcast candle update to all connected clients."""
        if not self.clients:
            return
        
        message = json.dumps({
            'type': 'candle_update',
            'data': {
                'symbol': candle_data['symbol'],
                'open': candle_data['open'],
                'high': candle_data['high'],
                'low': candle_data['low'],
                'close': candle_data['close'],
                'open_time': candle_data['open_time'].isoformat(),
                'close_time': candle_data['close_time'].isoformat(),
                'volume': candle_data.get('volume', 0),
                'is_finalized': candle_data.get('is_finalized', False)
            },
            'timestamp': datetime.now().isoformat()
        })
        
        # Broadcast to all clients
        disconnected = set()
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(client)
        
        # Remove disconnected clients
        for client in disconnected:
            await self.unregister(client)
    
    async def handler(self, websocket: websockets.WebSocketServerProtocol):
        """Handle WebSocket connection."""
        await self.register(websocket)
        try:
            async for message in websocket:
                # Handle client messages (e.g., subscribe to specific symbols)
                try:
                    data = json.loads(message)
                    if data.get('type') == 'subscribe':
                        symbol = data.get('symbol')
                        logger.info(f"Client subscribed to {symbol}")
                        # Handle subscription logic here
                except json.JSONDecodeError:
                    logger.error(f"Invalid message format: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
    
    async def start(self):
        """Start WebSocket server with port fallback."""
        # Try the configured port first
        if self.is_port_available(self.port):
            try:
                self.server = await websockets.serve(
                    self.handler,
                    self.host,
                    self.port
                )
                logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
                return
            except Exception as e:
                logger.warning(f"Could not start on port {self.port}: {e}")
        
        # Try alternative ports
        for alt_port in [8766, 8767, 8768, 8769, 8770]:
            if self.is_port_available(alt_port):
                try:
                    self.server = await websockets.serve(
                        self.handler,
                        self.host,
                        alt_port
                    )
                    logger.info(f"WebSocket server started on ws://{self.host}:{alt_port} (fallback)")
                    self.port = alt_port
                    settings.WS_PORT = alt_port  # Update settings
                    return
                except Exception as e:
                    continue
        
        logger.error("Could not start WebSocket server on any port")
        raise RuntimeError("No available ports for WebSocket server")
    
    async def stop(self):
        """Stop WebSocket server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped")