"""Device management service layer [M1]."""
from datetime import datetime, timezone
import threading
import uuid
from typing import Dict, List, Optional, Any

from app.devices.schemas import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    CameraStatus,
    DeviceHeartbeat,
)


class DeviceService:
    """Service managing camera device registration, metadata, and connection states.
    
    Provides thread-safe in-memory caching and persistence hooks, allowing complete
    functional independence while providing clean contracts for PostgreSQL integration.
    """

    def __init__(self) -> None:
        self._devices: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def register_device_sync(self, data: DeviceCreate) -> DeviceResponse:
        """Synchronous implementation of device registration."""
        with self._lock:
            now = datetime.now(timezone.utc)
            device_id = str(uuid.uuid4())
            record: Dict[str, Any] = {
                "id": device_id,
                "name": data.name,
                "location": data.location,
                "latitude": data.latitude,
                "longitude": data.longitude,
                "status": CameraStatus.OFFLINE,
                "is_active": True,
                "device_metadata": data.device_metadata or {},
                "created_at": now,
                "updated_at": now,
                "last_seen_at": None,
            }
            self._devices[device_id] = record
            return DeviceResponse(**record)

    async def register_device(self, data: DeviceCreate) -> DeviceResponse:
        """Register a new camera device."""
        return self.register_device_sync(data)

    def list_devices_sync(
        self,
        status: Optional[CameraStatus] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> List[DeviceResponse]:
        """Synchronous implementation of listing registered cameras."""
        with self._lock:
            results: List[DeviceResponse] = []
            for record in self._devices.values():
                if status is not None and record["status"] != status:
                    continue
                if is_active is not None and record["is_active"] != is_active:
                    continue
                if search:
                    s = search.lower()
                    if s not in record["name"].lower() and s not in record["location"].lower():
                        continue
                results.append(DeviceResponse(**record))
            results.sort(key=lambda d: d.created_at, reverse=True)
            return results

    async def list_devices(
        self,
        status: Optional[CameraStatus] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> List[DeviceResponse]:
        """List registered cameras with optional filtering."""
        return self.list_devices_sync(status=status, is_active=is_active, search=search)

    def get_device_sync(self, device_id: str) -> Optional[DeviceResponse]:
        """Synchronously retrieve a specific camera device by ID."""
        with self._lock:
            record = self._devices.get(device_id)
            if not record:
                return None
            return DeviceResponse(**record)

    async def get_device(self, device_id: str) -> Optional[DeviceResponse]:
        """Retrieve a specific camera device by ID."""
        return self.get_device_sync(device_id)

    def update_device_sync(self, device_id: str, data: DeviceUpdate) -> Optional[DeviceResponse]:
        """Synchronously update an existing camera device's metadata or status."""
        with self._lock:
            record = self._devices.get(device_id)
            if not record:
                return None

            now = datetime.now(timezone.utc)
            if data.name is not None:
                record["name"] = data.name
            if data.location is not None:
                record["location"] = data.location
            if data.latitude is not None:
                record["latitude"] = data.latitude
            if data.longitude is not None:
                record["longitude"] = data.longitude
            if data.status is not None:
                record["status"] = data.status
            if data.is_active is not None:
                record["is_active"] = data.is_active
            if data.device_metadata is not None:
                record["device_metadata"].update(data.device_metadata)

            record["updated_at"] = now
            return DeviceResponse(**record)

    async def update_device(self, device_id: str, data: DeviceUpdate) -> Optional[DeviceResponse]:
        """Update an existing camera device's metadata or status."""
        return self.update_device_sync(device_id, data)

    def deactivate_device_sync(self, device_id: str, hard_delete: bool = False) -> Optional[DeviceResponse]:
        """Synchronously deactivate or safely delete a camera device."""
        with self._lock:
            record = self._devices.get(device_id)
            if not record:
                return None

            if hard_delete:
                del self._devices[device_id]
                return DeviceResponse(**record)

            now = datetime.now(timezone.utc)
            record["is_active"] = False
            record["status"] = CameraStatus.OFFLINE
            record["updated_at"] = now
            return DeviceResponse(**record)

    async def deactivate_device(self, device_id: str, hard_delete: bool = False) -> Optional[DeviceResponse]:
        """Deactivate or safely delete a camera device."""
        return self.deactivate_device_sync(device_id, hard_delete=hard_delete)

    def record_heartbeat_sync(self, device_id: str, heartbeat: DeviceHeartbeat) -> Optional[DeviceResponse]:
        """Synchronously record a heartbeat and update status for an online camera."""
        with self._lock:
            record = self._devices.get(device_id)
            if not record:
                return None

            now = datetime.now(timezone.utc)
            record["status"] = heartbeat.status
            record["last_seen_at"] = now
            record["updated_at"] = now
            if heartbeat.device_metadata:
                record["device_metadata"].update(heartbeat.device_metadata)
            return DeviceResponse(**record)

    async def record_heartbeat(self, device_id: str, heartbeat: DeviceHeartbeat) -> Optional[DeviceResponse]:
        """Record a heartbeat and update status for an online camera."""
        return self.record_heartbeat_sync(device_id, heartbeat)

    def clear_all_sync(self) -> None:
        """Synchronously clear all devices in memory."""
        with self._lock:
            self._devices.clear()

    async def clear_all(self) -> None:
        """Clear all devices in memory (useful for test fixtures)."""
        self.clear_all_sync()


# Global default service singleton
device_service = DeviceService()
