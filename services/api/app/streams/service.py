"""Stream management service layer [M1]."""
from datetime import datetime, timezone
import os
import threading
import uuid
from typing import Dict, List, Optional, Any

from app.streams.schemas import (
    StreamStatus,
    StreamStartRequest,
    StreamStopRequest,
    StreamStatusUpdate,
    StreamHeartbeat,
    StreamResponse,
)
from app.devices.service import device_service
from app.devices.schemas import CameraStatus, DeviceHeartbeat


class DuplicateStreamSessionError(Exception):
    """Raised when starting a stream on a device with an existing active stream."""
    pass


class DeviceNotFoundError(Exception):
    """Raised when device_id is not registered."""
    pass


class DeviceInactiveError(Exception):
    """Raised when attempting to stream from a deactivated device."""
    pass


class StreamService:
    """Service managing camera streaming sessions, MediaMTX URLs, and stream lifecycle."""

    def __init__(self) -> None:
        self._streams: Dict[str, Dict[str, Any]] = {}
        self._device_to_stream: Dict[str, str] = {}
        self._lock = threading.Lock()

    def _resolve_endpoints(self, device_id: str) -> Dict[str, str]:
        """Generate gateway endpoints for publishing (WHIP) and consumption (RTSP/WHEP/HLS)."""
        stream_path = f"live/{device_id}"

        webrtc_base = os.getenv("MEDIAMTX_WEBRTC_URL", "http://localhost:8889").rstrip("/")
        rtsp_base = os.getenv("MEDIAMTX_RTSP_URL", "rtsp://video-gateway:8554").rstrip("/")
        hls_base = os.getenv("MEDIAMTX_HLS_URL", "http://localhost:8888").rstrip("/")

        return {
            "stream_path": stream_path,
            "whip_url": f"{webrtc_base}/{stream_path}/whip",
            "whep_url": f"{webrtc_base}/{stream_path}/whep",
            "rtsp_url": f"{rtsp_base}/{stream_path}",
            "hls_url": f"{hls_base}/{stream_path}/index.m3u8",
        }

    def start_stream_sync(self, data: StreamStartRequest) -> StreamResponse:
        """Synchronously initiate or recover a streaming session for a camera device."""
        with self._lock:
            device = device_service.get_device_sync(data.device_id)
            if not device:
                raise DeviceNotFoundError(f"Device '{data.device_id}' does not exist.")
            if not device.is_active:
                raise DeviceInactiveError(f"Device '{data.device_id}' is deactivated.")

            now = datetime.now(timezone.utc)
            existing_stream_id = self._device_to_stream.get(data.device_id)

            if existing_stream_id:
                existing = self._streams.get(existing_stream_id)
                if existing and existing["status"] in (StreamStatus.LIVE, StreamStatus.STARTING, StreamStatus.RECONNECTING):
                    if not data.force_restart:
                        raise DuplicateStreamSessionError(
                            f"An active stream session '{existing_stream_id}' already exists for device '{data.device_id}'."
                        )
                    existing["status"] = StreamStatus.STOPPED
                    existing["ended_at"] = now
                    existing["error_message"] = "Replaced by forced restart session"

            stream_id = str(uuid.uuid4())
            endpoints = self._resolve_endpoints(data.device_id)

            record: Dict[str, Any] = {
                "id": stream_id,
                "device_id": data.device_id,
                "status": StreamStatus.STARTING,
                "stream_path": endpoints["stream_path"],
                "whip_url": endpoints["whip_url"],
                "whep_url": endpoints["whep_url"],
                "rtsp_url": endpoints["rtsp_url"],
                "hls_url": endpoints["hls_url"],
                "started_at": now,
                "ended_at": None,
                "error_message": None,
                "reconnect_attempts": 0,
                "stream_metadata": data.stream_metadata or {},
            }

            self._streams[stream_id] = record
            self._device_to_stream[data.device_id] = stream_id

            device_service.record_heartbeat_sync(
                data.device_id,
                DeviceHeartbeat(status=CameraStatus.ONLINE)
            )

            return StreamResponse(**record)

    async def start_stream(self, data: StreamStartRequest) -> StreamResponse:
        """Initiate or recover a streaming session for a camera device."""
        return self.start_stream_sync(data)

    def stop_stream_sync(self, data: StreamStopRequest) -> Optional[StreamResponse]:
        """Synchronously stop an active stream session by stream_id or device_id."""
        with self._lock:
            stream_id = data.stream_id
            if not stream_id and data.device_id:
                stream_id = self._device_to_stream.get(data.device_id)

            if not stream_id or stream_id not in self._streams:
                return None

            record = self._streams[stream_id]
            now = datetime.now(timezone.utc)
            record["status"] = StreamStatus.STOPPED
            record["ended_at"] = now
            record["error_message"] = data.reason

            dev_id = record["device_id"]
            if self._device_to_stream.get(dev_id) == stream_id:
                self._device_to_stream.pop(dev_id, None)

            device_service.record_heartbeat_sync(
                dev_id,
                DeviceHeartbeat(status=CameraStatus.OFFLINE)
            )

            return StreamResponse(**record)

    async def stop_stream(self, data: StreamStopRequest) -> Optional[StreamResponse]:
        """Stop an active stream session by stream_id or device_id."""
        return self.stop_stream_sync(data)

    def get_stream_sync(self, stream_id: str) -> Optional[StreamResponse]:
        """Synchronously retrieve stream session details by ID."""
        with self._lock:
            record = self._streams.get(stream_id)
            if not record:
                return None
            return StreamResponse(**record)

    async def get_stream(self, stream_id: str) -> Optional[StreamResponse]:
        """Retrieve stream session details by ID."""
        return self.get_stream_sync(stream_id)

    def get_device_stream_sync(self, device_id: str) -> Optional[StreamResponse]:
        """Synchronously retrieve the currently active stream for a specific device."""
        with self._lock:
            stream_id = self._device_to_stream.get(device_id)
            if not stream_id:
                device_streams = [s for s in self._streams.values() if s["device_id"] == device_id]
                if not device_streams:
                    return None
                device_streams.sort(key=lambda x: x["started_at"], reverse=True)
                return StreamResponse(**device_streams[0])

            record = self._streams.get(stream_id)
            if not record:
                return None
            return StreamResponse(**record)

    async def get_device_stream(self, device_id: str) -> Optional[StreamResponse]:
        """Retrieve the currently active stream for a specific device."""
        return self.get_device_stream_sync(device_id)

    def list_streams_sync(self, status: Optional[StreamStatus] = None) -> List[StreamResponse]:
        """Synchronously list all stream sessions with optional status filtering."""
        with self._lock:
            results: List[StreamResponse] = []
            for record in self._streams.values():
                if status is not None and record["status"] != status:
                    continue
                results.append(StreamResponse(**record))
            results.sort(key=lambda s: s.started_at, reverse=True)
            return results

    async def list_streams(self, status: Optional[StreamStatus] = None) -> List[StreamResponse]:
        """List all stream sessions with optional status filtering."""
        return self.list_streams_sync(status=status)

    def update_status_sync(self, stream_id: str, payload: StreamStatusUpdate) -> Optional[StreamResponse]:
        """Synchronously update stream status."""
        with self._lock:
            record = self._streams.get(stream_id)
            if not record:
                return None

            record["status"] = payload.status
            if payload.error_message:
                record["error_message"] = payload.error_message

            dev_id = record["device_id"]
            if payload.status == StreamStatus.LIVE:
                record["error_message"] = None
                device_service.record_heartbeat_sync(
                    dev_id,
                    DeviceHeartbeat(status=CameraStatus.ONLINE)
                )
            elif payload.status == StreamStatus.RECONNECTING:
                record["reconnect_attempts"] += 1
                device_service.record_heartbeat_sync(
                    dev_id,
                    DeviceHeartbeat(status=CameraStatus.RECONNECTING)
                )
            elif payload.status == StreamStatus.FAILED:
                now = datetime.now(timezone.utc)
                record["ended_at"] = now
                device_service.record_heartbeat_sync(
                    dev_id,
                    DeviceHeartbeat(status=CameraStatus.ERROR)
                )
            elif payload.status == StreamStatus.STOPPED:
                now = datetime.now(timezone.utc)
                record["ended_at"] = now
                if self._device_to_stream.get(dev_id) == stream_id:
                    self._device_to_stream.pop(dev_id, None)
                device_service.record_heartbeat_sync(
                    dev_id,
                    DeviceHeartbeat(status=CameraStatus.OFFLINE)
                )

            return StreamResponse(**record)

    async def update_status(self, stream_id: str, payload: StreamStatusUpdate) -> Optional[StreamResponse]:
        """Update stream status (e.g. from STARTING to LIVE, or RECONNECTING/FAILED)."""
        return self.update_status_sync(stream_id, payload)

    def record_heartbeat_sync(self, stream_id: str, payload: StreamHeartbeat) -> Optional[StreamResponse]:
        """Synchronously record a heartbeat on an active stream session."""
        with self._lock:
            record = self._streams.get(stream_id)
            if not record:
                return None

            if payload.stats:
                record["stream_metadata"]["last_stats"] = payload.stats
                record["stream_metadata"]["last_stats_at"] = datetime.now(timezone.utc).isoformat()

            if record["status"] != payload.status:
                record["status"] = payload.status

            dev_id = record["device_id"]
            device_service.record_heartbeat_sync(
                dev_id,
                DeviceHeartbeat(status=CameraStatus.ONLINE)
            )

            return StreamResponse(**record)

    async def record_heartbeat(self, stream_id: str, payload: StreamHeartbeat) -> Optional[StreamResponse]:
        """Record a heartbeat on an active stream session."""
        return self.record_heartbeat_sync(stream_id, payload)

    def clear_all_sync(self) -> None:
        """Synchronously clear all stream records in memory."""
        with self._lock:
            self._streams.clear()
            self._device_to_stream.clear()

    async def clear_all(self) -> None:
        """Clear all stream records in memory (for test fixtures)."""
        self.clear_all_sync()


# Global default stream service singleton
stream_service = StreamService()
