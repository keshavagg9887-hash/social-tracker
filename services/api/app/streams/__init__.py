"""[M1] Live video stream endpoints & proxies."""
from app.streams.schemas import (
    StreamStatus,
    StreamStartRequest,
    StreamStopRequest,
    StreamStatusUpdate,
    StreamHeartbeat,
    StreamResponse,
    StreamListResponse,
)
from app.streams.service import (
    StreamService,
    stream_service,
    DuplicateStreamSessionError,
    DeviceNotFoundError,
    DeviceInactiveError,
)
from app.streams.router import router

__all__ = [
    "StreamStatus",
    "StreamStartRequest",
    "StreamStopRequest",
    "StreamStatusUpdate",
    "StreamHeartbeat",
    "StreamResponse",
    "StreamListResponse",
    "StreamService",
    "stream_service",
    "DuplicateStreamSessionError",
    "DeviceNotFoundError",
    "DeviceInactiveError",
    "router",
]
