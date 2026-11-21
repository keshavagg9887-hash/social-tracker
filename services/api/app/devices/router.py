"""Edge / Camera Device Registration & Management Router [M1/M3 Integration]."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.security import get_current_user, require_roles
from ..database.models import Camera, User
from ..database.session import get_db

router = APIRouter(prefix="/devices", tags=["Camera Devices"])


class CameraDeviceCreate(BaseModel):
    id: str = Field(..., description="Unique device identifier or serial")
    name: str = Field(..., description="Human readable camera name")
    rtsp_url: str = Field(..., description="RTSP or WebRTC stream ingestion URL")
    location: str = Field(..., description="Physical location or zone")
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CameraDeviceResponse(BaseModel):
    id: str
    name: str
    rtspUrl: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    isActive: bool
    status: str
    lastSeen: Optional[str] = None
    createdAt: Optional[str] = None


@router.get("", response_model=List[CameraDeviceResponse], summary="List Registered Cameras")
async def list_cameras(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[CameraDeviceResponse]:
    stmt = select(Camera).order_by(Camera.created_at.desc())
    result = await db.execute(stmt)
    cameras = result.scalars().all()
    return [CameraDeviceResponse(**c.to_dict()) for c in cameras]


@router.post("", response_model=CameraDeviceResponse, status_code=status.HTTP_201_CREATED, summary="Register Camera")
async def register_camera(
    payload: CameraDeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "handler")),
) -> CameraDeviceResponse:
    stmt = select(Camera).where(Camera.id == payload.id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Camera ID already registered")

    camera = Camera(
        id=payload.id,
        name=payload.name,
        rtsp_url=payload.rtsp_url,
        location=payload.location,
        latitude=payload.latitude,
        longitude=payload.longitude,
        status="online",
        is_active=True,
    )
    db.add(camera)
    await db.commit()
    await db.refresh(camera)
    return CameraDeviceResponse(**camera.to_dict())


@router.get("/{camera_id}", response_model=CameraDeviceResponse, summary="Get Camera Details")
async def get_camera(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CameraDeviceResponse:
    stmt = select(Camera).where(Camera.id == camera_id)
    result = await db.execute(stmt)
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    return CameraDeviceResponse(**camera.to_dict())
