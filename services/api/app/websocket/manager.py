"""Real-time WebSocket Connection Manager [M3].

Maintains active connections from Handler Dashboards and broadcasts real-time
incident candidates, verification updates, and assignment notifications.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections with broadcast and channel filters."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept incoming connection and register in active pool."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove disconnected client from active pool."""
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast JSON payload to all connected clients."""
        if not self.active_connections:
            return

        payload_str = json.dumps(message)
        async with self._lock:
            stale_connections = set()
            for connection in self.active_connections:
                try:
                    await connection.send_text(payload_str)
                except Exception as e:
                    logger.warning(f"Failed to send to WebSocket client: {e}")
                    stale_connections.add(connection)

            # Cleanup stale connections
            self.active_connections.difference_update(stale_connections)

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket) -> None:
        """Send message directly to a single socket."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.warning(f"Error sending personal message: {e}")


ws_manager = ConnectionManager()
