"""Pydantic schemas for Stream Management [M1]."""
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class StreamStatus(str, Enum):
    """Permitted live streaming lifecycle statuses."""
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    LIVE = "LIVE"
    RECONNECTING = "RECONNECTING"
    FAILED = "FAILED"


class StreamStartRequest(BaseModel):
    """Payload to initiate a video stream for a camera device."""
    device_id: str = Field(..., description="UUID of registered camera device")
    force_restart: bool = Field(False, description="If True, terminate existing live session and restart")
    stream_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Stream client parameters")


class StreamStopRequest(BaseModel):
    """Payload to stop a video stream session."""
    device_id: Optional[str] = Field(None, description="UUID of camera device")
    stream_id: Optional[str] = Field(None, description="UUID of stream session")
    reason: Optional[str] = Field("User initiated stop", description="Reason for stopping stream")


class StreamStatusUpdate(BaseModel):
    """Payload to update streaming state from client or video gateway."""
    status: StreamStatus = Field(..., description="Target stream lifecycle status")
    error_message: Optional[str] = Field(None, description="Details if status is FAILED or RECONNECTING")


class StreamHeartbeat(BaseModel):
    """Payload for keeping an active stream session alive."""
    status: StreamStatus = StreamStatus.LIVE
    stats: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Client WebRTC statistics")


class StreamResponse(BaseModel):
    """Complete streaming session representation."""
    id: str
    device_id: str
    status: StreamStatus
    stream_path: str
    whip_url: str
    whep_url: str
    rtsp_url: str
    hls_url: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    error_message: Optional[str] = None
    reconnect_attempts: int = 0
    stream_metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "from_attributes": True
    }


class StreamListResponse(BaseModel):
    """List of stream sessions."""
    items: List[StreamResponse]
    total: int

