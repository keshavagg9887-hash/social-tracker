"""Live Video Streams Gateway & Proxy Router [M1/M3 Integration]."""

from fastapi import APIRouter, Depends
from ..auth.security import get_current_user
from ..database.models import User

router = APIRouter(prefix="/streams", tags=["Video Streams"])


@router.get("/health", summary="Video Gateway Health Proxy")
async def stream_gateway_health(current_user: User = Depends(get_current_user)):
    return {
        "status": "healthy",
        "gateway": "MediaMTX",
        "protocols": ["WebRTC", "RTSP", "HLS"],
    }
