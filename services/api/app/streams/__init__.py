"""Streams Package [M1/M3 Integrated].

Provides live video stream session management, MediaMTX WebRTC (WHIP/WHEP),
RTSP, and HLS gateway endpoints.
"""

from .schemas import (
    StreamStatus,
    StreamStartRequest,
    StreamStopRequest,
    StreamStatusUpdate,
    StreamHeartbeat,
    StreamResponse,
    StreamListResponse,
)
from .service import (
    StreamService,
    stream_service,
    DuplicateStreamSessionError,
    DeviceNotFoundError,
    DeviceInactiveError,
)
from .router import router

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
