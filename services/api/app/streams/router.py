"""FastAPI router for Stream Management [M1]."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.streams.schemas import (
    StreamStatus,
    StreamStartRequest,
    StreamStopRequest,
    StreamStatusUpdate,
    StreamHeartbeat,
    StreamResponse,
)
from app.streams.service import (
    stream_service,
    DuplicateStreamSessionError,
    DeviceNotFoundError,
    DeviceInactiveError,
)

router = APIRouter(prefix="", tags=["Stream Management"])


@router.post(
    "/start",
    response_model=StreamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start camera stream session",
    description="Initiates a live streaming session for a camera and returns MediaMTX WebRTC (WHIP/WHEP), RTSP, and HLS endpoints.",
)
async def start_stream(payload: StreamStartRequest) -> StreamResponse:
    try:
        return await stream_service.start_stream(payload)
    except DeviceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DeviceInactiveError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DuplicateStreamSessionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/stop",
    response_model=StreamResponse,
    summary="Stop camera stream session",
    description="Terminates an active streaming session by stream_id or device_id and resets device status.",
)
async def stop_stream(payload: StreamStopRequest) -> StreamResponse:
    stopped = await stream_service.stop_stream(payload)
    if not stopped:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active stream session found matching the provided stream_id or device_id.",
        )
    return stopped


@router.get(
    "/",
    response_model=List[StreamResponse],
    summary="List streaming sessions",
    description="Returns all stream sessions with optional status filter.",
)
async def list_streams(
    status: Optional[StreamStatus] = Query(None, description="Filter streams by status (e.g. LIVE, STOPPED)"),
) -> List[StreamResponse]:
    return await stream_service.list_streams(status=status)


@router.get(
    "/{stream_id}",
    response_model=StreamResponse,
    summary="Get stream session details",
    description="Returns full metadata, URLs, and current status of a specific stream session.",
)
async def get_stream(stream_id: str) -> StreamResponse:
    stream = await stream_service.get_stream(stream_id)
    if not stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stream session '{stream_id}' was not found.",
        )
    return stream


@router.get(
    "/device/{device_id}",
    response_model=StreamResponse,
    summary="Get device's current stream",
    description="Returns the current or most recent stream session for a camera device.",
)
async def get_device_stream(device_id: str) -> StreamResponse:
    stream = await stream_service.get_device_stream(device_id)
    if not stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No stream found for device '{device_id}'.",
        )
    return stream


@router.post(
    "/{stream_id}/status",
    response_model=StreamResponse,
    summary="Update stream session status",
    description="Allows client or gateway to report state changes (e.g., transition to LIVE, RECONNECTING, or FAILED).",
)
async def update_stream_status(stream_id: str, payload: StreamStatusUpdate) -> StreamResponse:
    updated = await stream_service.update_status(stream_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stream session '{stream_id}' was not found.",
        )
    return updated


@router.post(
    "/{stream_id}/heartbeat",
    response_model=StreamResponse,
    summary="Stream session keepalive heartbeat",
    description="Reports client WebRTC statistics and keeps the live session active.",
)
async def stream_heartbeat(stream_id: str, payload: StreamHeartbeat) -> StreamResponse:
    updated = await stream_service.record_heartbeat(stream_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stream session '{stream_id}' was not found.",
        )
    return updated

