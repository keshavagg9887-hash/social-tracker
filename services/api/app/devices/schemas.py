"""Pydantic schemas for Device Management [M1]."""
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator


class CameraStatus(str, Enum):
    """Permitted camera connection statuses."""
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    RECONNECTING = "RECONNECTING"
    ERROR = "ERROR"


class DeviceCreate(BaseModel):
    """Payload for registering a new camera device."""
    name: str = Field(..., min_length=1, max_length=255, description="Human-readable camera name")
    location: str = Field(..., min_length=1, max_length=255, description="Physical location description")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="WGS84 latitude")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="WGS84 longitude")
    device_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Hardware/browser metadata")

    @field_validator("name", "location")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or whitespace only")
        return stripped


class DeviceUpdate(BaseModel):
    """Payload for updating camera information."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    location: Optional[str] = Field(None, min_length=1, max_length=255)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    status: Optional[CameraStatus] = None
    is_active: Optional[bool] = None
    device_metadata: Optional[Dict[str, Any]] = None

    @field_validator("name", "location")
    @classmethod
    def strip_whitespace_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Field cannot be whitespace only")
            return stripped
        return v


class DeviceHeartbeat(BaseModel):
    """Payload for camera heartbeat / status reporting."""
    status: CameraStatus = CameraStatus.ONLINE
    device_metadata: Optional[Dict[str, Any]] = None


class DeviceResponse(BaseModel):
    """Response model for a registered camera device."""
    id: str
    name: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: CameraStatus
    is_active: bool
    device_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    last_seen_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }


class DeviceListResponse(BaseModel):
    """Paginated or listed response of camera devices."""
    items: List[DeviceResponse]
    total: int

