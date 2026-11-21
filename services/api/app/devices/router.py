"""FastAPI router for Device Management [M1]."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.devices.schemas import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    CameraStatus,
    DeviceHeartbeat,
)
from app.devices.service import device_service

router = APIRouter(prefix="", tags=["Device Management"])


@router.post(
    "/",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new camera device",
    description="Registers a new laptop/USB webcam device with location coordinates and metadata.",
)
async def register_camera(payload: DeviceCreate) -> DeviceResponse:
    return await device_service.register_device(payload)


@router.get(
    "/",
    response_model=List[DeviceResponse],
    summary="List registered camera devices",
    description="Returns all registered cameras with optional status, active state, and name/location search filters.",
)
async def list_cameras(
    status: Optional[CameraStatus] = Query(None, description="Filter by camera status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search term matching camera name or location"),
) -> List[DeviceResponse]:
    return await device_service.list_devices(status=status, is_active=is_active, search=search)


@router.get(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Retrieve camera device details",
    description="Returns full information and current connection status for a specific camera ID.",
)
async def get_camera(device_id: str) -> DeviceResponse:
    device = await device_service.get_device(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera device '{device_id}' was not found.",
        )
    return device


@router.patch(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Update camera device details",
    description="Updates camera name, location, coordinates, metadata, or status.",
)
async def update_camera(device_id: str, payload: DeviceUpdate) -> DeviceResponse:
    updated = await device_service.update_device(device_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera device '{device_id}' was not found.",
        )
    return updated


@router.delete(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Deactivate or delete a camera device",
    description="Deactivates a camera (soft delete) or removes it permanently if hard_delete=True.",
)
async def delete_camera(
    device_id: str,
    hard_delete: bool = Query(False, description="Set True to permanently delete the camera record"),
) -> DeviceResponse:
    deleted = await device_service.deactivate_device(device_id, hard_delete=hard_delete)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera device '{device_id}' was not found.",
        )
    return deleted


@router.post(
    "/{device_id}/heartbeat",
    response_model=DeviceResponse,
    summary="Record camera heartbeat",
    description="Updates the camera connection status and last_seen timestamp.",
)
async def record_camera_heartbeat(device_id: str, payload: DeviceHeartbeat) -> DeviceResponse:
    updated = await device_service.record_heartbeat(device_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera device '{device_id}' was not found.",
        )
    return updated

