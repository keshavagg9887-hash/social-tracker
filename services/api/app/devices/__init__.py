"""Devices Package [M1/M3 Integrated].

Provides camera/edge device registration, metadata, connection status,
and database integration.
"""

from .schemas import (
    CameraStatus,
    DeviceCreate,
    DeviceUpdate,
    DeviceHeartbeat,
    DeviceResponse,
    DeviceListResponse,
)
from .models import CameraDeviceModel
from .service import DeviceService, device_service
from .router import router, CameraDeviceCreate, CameraDeviceResponse

__all__ = [
    "CameraStatus",
    "DeviceCreate",
    "DeviceUpdate",
    "DeviceHeartbeat",
    "DeviceResponse",
    "DeviceListResponse",
    "CameraDeviceCreate",
    "CameraDeviceResponse",
    "CameraDeviceModel",
    "DeviceService",
    "device_service",
    "router",
]
