"""WebSocket Router for Real-time Feeds [M3].

Provides the `/ws/incidents` endpoint for live streaming of AI candidates,
incident lifecycle changes, and responder assignments.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .manager import ws_manager

router = APIRouter(tags=["WebSocket Feeds"])


@router.websocket("/ws/incidents")
async def websocket_incidents_endpoint(websocket: WebSocket):
    """WebSocket stream for Handler Dashboards."""
    await ws_manager.connect(websocket)
    try:
        # Send initial connection handshake
        await ws_manager.send_personal_message(
            {
                "type": "connection_established",
                "message": "Connected to real-time incident event stream",
            },
            websocket,
        )

        while True:
            # Keep connection open, handle client heartbeats or ping messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception:
        await ws_manager.disconnect(websocket)
