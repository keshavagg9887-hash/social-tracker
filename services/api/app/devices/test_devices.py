"""Comprehensive unit & validation tests for Device Management [M1]."""
import pytest
from pydantic import ValidationError

from app.devices.service import device_service
from app.devices.schemas import (
    DeviceCreate,
    DeviceUpdate,
    DeviceHeartbeat,
    CameraStatus,
)


@pytest.fixture(autouse=True)
def clean_devices():
    """Ensure in-memory device store is clean before each test."""
    device_service.clear_all_sync()
    yield
    device_service.clear_all_sync()


def test_register_device_success():
    payload = DeviceCreate(
        name="Lobby Webcam A",
        location="HQ First Floor Reception",
        latitude=37.7749,
        longitude=-122.4194,
        device_metadata={"resolution": "1080p", "fps": 30},
    )
    dev = device_service.register_device_sync(payload)

    assert dev.id is not None
    assert dev.name == "Lobby Webcam A"
    assert dev.location == "HQ First Floor Reception"
    assert dev.latitude == 37.7749
    assert dev.longitude == -122.4194
    assert dev.status == CameraStatus.OFFLINE
    assert dev.is_active is True
    assert dev.device_metadata["fps"] == 30
    assert dev.created_at is not None


def test_register_device_validation_errors():
    # Latitude > 90
    with pytest.raises(ValidationError):
        DeviceCreate(name="Bad Lat", location="Somewhere", latitude=95.0)

    # Latitude < -90
    with pytest.raises(ValidationError):
        DeviceCreate(name="Bad Lat", location="Somewhere", latitude=-95.0)

    # Longitude > 180
    with pytest.raises(ValidationError):
        DeviceCreate(name="Bad Lng", location="Somewhere", longitude=185.0)

    # Empty name
    with pytest.raises(ValidationError):
        DeviceCreate(name="   ", location="Somewhere")

    # Empty location
    with pytest.raises(ValidationError):
        DeviceCreate(name="Valid Name", location="   ")


def test_list_devices_and_filtering():
    device_service.register_device_sync(DeviceCreate(
        name="Parking Entrance",
        location="Garage Level 1",
    ))
    device_service.register_device_sync(DeviceCreate(
        name="Roof Perimeter",
        location="Building Rooftop",
    ))

    # All devices
    items = device_service.list_devices_sync()
    assert len(items) == 2

    # Filter by search
    searched = device_service.list_devices_sync(search="parking")
    assert len(searched) == 1
    assert searched[0].name == "Parking Entrance"

    # Filter by status
    offline = device_service.list_devices_sync(status=CameraStatus.OFFLINE)
    assert len(offline) == 2
    online = device_service.list_devices_sync(status=CameraStatus.ONLINE)
    assert len(online) == 0


def test_get_device_by_id():
    created = device_service.register_device_sync(DeviceCreate(
        name="Hallway Cam",
        location="West Wing Corridor",
    ))

    retrieved = device_service.get_device_sync(created.id)
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.name == "Hallway Cam"

    # Non-existent ID returns None
    missing = device_service.get_device_sync("non-existent-uuid")
    assert missing is None


def test_update_device():
    created = device_service.register_device_sync(DeviceCreate(
        name="Old Name",
        location="Old Location",
    ))

    updated = device_service.update_device_sync(
        created.id,
        DeviceUpdate(
            name="Updated Name",
            location="New Location",
            latitude=40.7128,
            longitude=-74.0060,
            status=CameraStatus.ONLINE,
        ),
    )
    assert updated is not None
    assert updated.name == "Updated Name"
    assert updated.location == "New Location"
    assert updated.latitude == 40.7128
    assert updated.longitude == -74.0060
    assert updated.status == CameraStatus.ONLINE


def test_deactivate_and_delete_device():
    created = device_service.register_device_sync(DeviceCreate(
        name="Temp Cam",
        location="Warehouse",
    ))

    # Soft delete (deactivate)
    deactivated = device_service.deactivate_device_sync(created.id, hard_delete=False)
    assert deactivated is not None
    assert deactivated.is_active is False
    assert deactivated.status == CameraStatus.OFFLINE

    # Hard delete
    hard_deleted = device_service.deactivate_device_sync(created.id, hard_delete=True)
    assert hard_deleted is not None

    # Should no longer exist
    assert device_service.get_device_sync(created.id) is None


def test_device_heartbeat():
    created = device_service.register_device_sync(DeviceCreate(
        name="Heartbeat Cam",
        location="Gate 3",
    ))

    hb = device_service.record_heartbeat_sync(
        created.id,
        DeviceHeartbeat(
            status=CameraStatus.ONLINE,
            device_metadata={"battery": "98%", "firmware": "v2.1"},
        ),
    )
    assert hb is not None
    assert hb.status == CameraStatus.ONLINE
    assert hb.last_seen_at is not None
    assert hb.device_metadata["battery"] == "98%"
    assert hb.device_metadata["firmware"] == "v2.1"
