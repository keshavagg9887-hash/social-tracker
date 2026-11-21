"""[M1] Edge/Camera device registration & status."""
from app.devices.schemas import (
    CameraStatus,
    DeviceCreate,
    DeviceUpdate,
    DeviceHeartbeat,
    DeviceResponse,
    DeviceListResponse,
)
from app.devices.models import CameraDeviceModel
from app.devices.service import DeviceService, device_service
from app.devices.router import router

__all__ = [
    "CameraStatus",
    "DeviceCreate",
    "DeviceUpdate",
    "DeviceHeartbeat",
    "DeviceResponse",
    "DeviceListResponse",
    "CameraDeviceModel",
    "DeviceService",
    "device_service",
    "router",
]
