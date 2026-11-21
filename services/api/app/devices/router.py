"""Edge / Camera Device Registration & Management Router [M1/M3 Integrated].

Combines:
- M1 Camera Client registration, WebRTC/MediaMTX endpoints, and hardware status
- M3 PostgreSQL/PostGIS database persistence and Role-Based Access Control
"""

from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from ..database.models import Camera, User
    from ..database.session import get_db
    from ..auth.security import get_current_user, require_roles, bearer_scheme
    HAVE_DB = True
except ImportError:
    AsyncSession = None
    Camera = None
    User = None
    get_db = None
    get_current_user = None
    require_roles = None
    bearer_scheme = None
    HAVE_DB = False

from .schemas import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    CameraStatus,
    DeviceHeartbeat,
)
from .service import device_service

router = APIRouter(prefix="/devices", tags=["Camera Devices"])


# ---------------------------------------------------------------------------
# Integrated Data Models (satisfying both M1 and M3/M4 contracts)
# ---------------------------------------------------------------------------
class CameraDeviceCreate(DeviceCreate):
    """Camera registration schema supporting optional custom id and rtsp_url."""
    id: Optional[str] = Field(None, description="Optional custom unique device identifier or serial")
    rtsp_url: Optional[str] = Field(None, description="Optional custom RTSP stream URL")


class CameraDeviceResponse(BaseModel):
    """Unified response containing both snake_case (M1) and camelCase (M3/M4) properties."""
    id: str
    name: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str
    is_active: bool = True
    isActive: bool = True
    rtsp_url: Optional[str] = None
    rtspUrl: str
    device_metadata: Dict[str, Any] = Field(default_factory=dict)
    last_seen_at: Optional[datetime] = None
    lastSeen: Optional[str] = None
    created_at: Optional[datetime] = None
    createdAt: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


def _build_unified_response(dev: Any, rtsp_url: Optional[str] = None) -> CameraDeviceResponse:
    """Format camera entity from either database model or in-memory service."""
    if hasattr(dev, "to_dict"):
        d = dev.to_dict()
        created_dt = dev.created_at if hasattr(dev, "created_at") else None
        last_seen_dt = dev.last_seen if hasattr(dev, "last_seen") else None
        url = d.get("rtspUrl") or d.get("rtsp_url") or rtsp_url or f"rtsp://video-gateway:8554/live/{dev.id}"
        return CameraDeviceResponse(
            id=dev.id,
            name=dev.name,
            location=dev.location,
            latitude=dev.latitude,
            longitude=dev.longitude,
            status=str(dev.status).upper(),
            is_active=dev.is_active,
            isActive=dev.is_active,
            rtsp_url=url,
            rtspUrl=url,
            device_metadata={},
            last_seen_at=last_seen_dt,
            lastSeen=d.get("lastSeen"),
            created_at=created_dt,
            createdAt=d.get("createdAt"),
            updated_at=getattr(dev, "updated_at", None),
        )

    # In-memory DeviceResponse
    url = getattr(dev, "rtsp_url", None) or rtsp_url or f"rtsp://video-gateway:8554/live/{dev.id}"
    return CameraDeviceResponse(
        id=dev.id,
        name=dev.name,
        location=dev.location,
        latitude=dev.latitude,
        longitude=dev.longitude,
        status=str(dev.status).upper() if hasattr(dev.status, "value") else str(dev.status),
        is_active=dev.is_active,
        isActive=dev.is_active,
        rtsp_url=url,
        rtspUrl=url,
        device_metadata=dev.device_metadata or {},
        last_seen_at=dev.last_seen_at,
        lastSeen=dev.last_seen_at.isoformat() if dev.last_seen_at else None,
        created_at=dev.created_at,
        createdAt=dev.created_at.isoformat() if dev.created_at else None,
        updated_at=dev.updated_at,
    )


# ---------------------------------------------------------------------------
# Optional Auth & DB Session Dependencies
# ---------------------------------------------------------------------------
async def _get_optional_db() -> AsyncGenerator:
    """Safely provide database session if available, otherwise yield None."""
    if not HAVE_DB or not get_db:
        yield None
        return
    try:
        from ..database.session import AsyncSessionLocal
        if AsyncSessionLocal is None:
            yield None
            return
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    except Exception:
        yield None


async def _get_optional_user(
    auth: Any = Depends(bearer_scheme) if bearer_scheme else None,
    db: Any = Depends(_get_optional_db),
) -> Optional[Any]:
    """Retrieve authenticated user if bearer credentials provided."""
    if not HAVE_DB or not auth or not getattr(auth, "credentials", None) or not db:
        return None
    try:
        return await get_current_user(auth, db)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Router Endpoints
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=List[CameraDeviceResponse],
    summary="List Registered Cameras",
    description="Returns all registered cameras with optional status, active state, and search filters.",
)
@router.get(
    "/",
    response_model=List[CameraDeviceResponse],
    include_in_schema=False,
)
async def list_cameras(
    status: Optional[CameraStatus] = Query(None, description="Filter by camera status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search term matching camera name or location"),
    db: Optional[Any] = Depends(_get_optional_db),
    current_user: Optional[Any] = Depends(_get_optional_user),
) -> List[CameraDeviceResponse]:
    # 1. Query database if available
    if db is not None and Camera is not None:
        try:
            stmt = select(Camera).order_by(Camera.created_at.desc())
            if is_active is not None:
                stmt = stmt.where(Camera.is_active == is_active)
            if status is not None:
                stmt = stmt.where(Camera.status == status.value.lower())
            if search:
                s = f"%{search.lower()}%"
                stmt = stmt.where(Camera.name.ilike(s) | Camera.location.ilike(s))

            result = await db.execute(stmt)
            db_cameras = result.scalars().all()
            if db_cameras:
                return [_build_unified_response(c) for c in db_cameras]
        except Exception:
            pass  # Fall back to in-memory store

    # 2. In-memory service fallback
    mem_cams = await device_service.list_devices(status=status, is_active=is_active, search=search)
    return [_build_unified_response(c) for c in mem_cams]


@router.post(
    "",
    response_model=CameraDeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Camera",
    description="Registers a new camera device with coordinates and persists to database and in-memory cache.",
)
@router.post(
    "/",
    response_model=CameraDeviceResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def register_camera(
    payload: CameraDeviceCreate,
    db: Optional[Any] = Depends(_get_optional_db),
    current_user: Optional[Any] = Depends(_get_optional_user),
) -> CameraDeviceResponse:
    # Enforce RBAC if user is authenticated
    if current_user is not None and getattr(current_user, "role", None) not in ("admin", "handler"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requires admin or handler role")

    # 1. Check duplicate ID in DB if explicit ID provided
    if payload.id and db is not None and Camera is not None:
        try:
            stmt = select(Camera).where(Camera.id == payload.id)
            res = await db.execute(stmt)
            if res.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Camera ID already registered")
        except HTTPException:
            raise
        except Exception:
            pass

    # 2. Register in service layer
    registered = await device_service.register_device(payload)
    device_id = payload.id or registered.id
    rtsp_url = payload.rtsp_url or f"rtsp://video-gateway:8554/live/{device_id}"

    # 3. Persist to database if available
    if db is not None and Camera is not None:
        try:
            cam = Camera(
                id=device_id,
                name=payload.name,
                rtsp_url=rtsp_url,
                location=payload.location,
                latitude=payload.latitude,
                longitude=payload.longitude,
                status="online",
                is_active=True,
            )
            db.add(cam)
            await db.commit()
            await db.refresh(cam)
            return _build_unified_response(cam)
        except Exception:
            pass

    return _build_unified_response(registered, rtsp_url=rtsp_url)


@router.get(
    "/{device_id}",
    response_model=CameraDeviceResponse,
    summary="Get Camera Details",
    description="Returns full information and current connection status for a specific camera ID.",
)
async def get_camera(
    device_id: str,
    db: Optional[Any] = Depends(_get_optional_db),
    current_user: Optional[Any] = Depends(_get_optional_user),
) -> CameraDeviceResponse:
    # 1. Try DB first
    if db is not None and Camera is not None:
        try:
            stmt = select(Camera).where(Camera.id == device_id)
            result = await db.execute(stmt)
            camera = result.scalar_one_or_none()
            if camera:
                return _build_unified_response(camera)
        except Exception:
            pass

    # 2. Try in-memory store
    device = await device_service.get_device(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera device '{device_id}' was not found.",
        )
    return _build_unified_response(device)


@router.patch(
    "/{device_id}",
    response_model=CameraDeviceResponse,
    summary="Update camera device details",
    description="Updates camera name, location, coordinates, metadata, or status.",
)
async def update_camera(
    device_id: str,
    payload: DeviceUpdate,
    db: Optional[Any] = Depends(_get_optional_db),
    current_user: Optional[Any] = Depends(_get_optional_user),
) -> CameraDeviceResponse:
    updated = await device_service.update_device(device_id, payload)

    # Sync to DB if available
    if db is not None and Camera is not None:
        try:
            stmt = select(Camera).where(Camera.id == device_id)
            res = await db.execute(stmt)
            cam = res.scalar_one_or_none()
            if cam:
                if payload.name:
                    cam.name = payload.name
                if payload.location:
                    cam.location = payload.location
                if payload.latitude is not None:
                    cam.latitude = payload.latitude
                if payload.longitude is not None:
                    cam.longitude = payload.longitude
                if payload.status:
                    cam.status = payload.status.value.lower()
                if payload.is_active is not None:
                    cam.is_active = payload.is_active
                await db.commit()
                await db.refresh(cam)
                return _build_unified_response(cam)
        except Exception:
            pass

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera device '{device_id}' was not found.",
        )
    return _build_unified_response(updated)


@router.delete(
    "/{device_id}",
    response_model=CameraDeviceResponse,
    summary="Deactivate or delete a camera device",
    description="Deactivates a camera (soft delete) or removes it permanently if hard_delete=True.",
)
async def delete_camera(
    device_id: str,
    hard_delete: bool = Query(False, description="Set True to permanently delete the camera record"),
    db: Optional[Any] = Depends(_get_optional_db),
    current_user: Optional[Any] = Depends(_get_optional_user),
) -> CameraDeviceResponse:
    deleted = await device_service.deactivate_device(device_id, hard_delete=hard_delete)

    # Sync to DB if available
    if db is not None and Camera is not None:
        try:
            stmt = select(Camera).where(Camera.id == device_id)
            res = await db.execute(stmt)
            cam = res.scalar_one_or_none()
            if cam:
                if hard_delete:
                    await db.delete(cam)
                else:
                    cam.is_active = False
                    cam.status = "offline"
                await db.commit()
                if not hard_delete:
                    await db.refresh(cam)
                    return _build_unified_response(cam)
        except Exception:
            pass

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera device '{device_id}' was not found.",
        )
    return _build_unified_response(deleted)


@router.post(
    "/{device_id}/heartbeat",
    response_model=CameraDeviceResponse,
    summary="Record camera heartbeat",
    description="Updates the camera connection status and last_seen timestamp.",
)
async def record_camera_heartbeat(
    device_id: str,
    payload: DeviceHeartbeat,
    db: Optional[Any] = Depends(_get_optional_db),
) -> CameraDeviceResponse:
    updated = await device_service.record_heartbeat(device_id, payload)

    if db is not None and Camera is not None:
        try:
            stmt = select(Camera).where(Camera.id == device_id)
            res = await db.execute(stmt)
            cam = res.scalar_one_or_none()
            if cam:
                cam.status = payload.status.value.lower()
                cam.last_seen = datetime.now(timezone.utc)
                await db.commit()
                await db.refresh(cam)
                return _build_unified_response(cam)
        except Exception:
            pass

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera device '{device_id}' was not found.",
        )
    return _build_unified_response(updated)
