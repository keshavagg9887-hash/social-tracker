"""Comprehensive unit & validation tests for Stream Management [M1]."""
import pytest
from app.devices.service import device_service
from app.devices.schemas import DeviceCreate, CameraStatus
from app.streams.service import (
    stream_service,
    DuplicateStreamSessionError,
    DeviceNotFoundError,
    DeviceInactiveError,
)
from app.streams.schemas import (
    StreamStatus,
    StreamStartRequest,
    StreamStopRequest,
    StreamStatusUpdate,
    StreamHeartbeat,
)


@pytest.fixture(autouse=True)
def clean_services():
    """Ensure in-memory device and stream stores are clean before each test."""
    device_service.clear_all_sync()
    stream_service.clear_all_sync()
    yield
    device_service.clear_all_sync()
    stream_service.clear_all_sync()


def test_start_stream_success():
    dev = device_service.register_device_sync(DeviceCreate(
        name="Traffic Cam 1",
        location="5th Ave & 42nd St",
    ))

    stream = stream_service.start_stream_sync(StreamStartRequest(device_id=dev.id))

    assert stream.id is not None
    assert stream.device_id == dev.id
    assert stream.status == StreamStatus.STARTING
    assert stream.stream_path == f"live/{dev.id}"
    assert f"/live/{dev.id}/whip" in stream.whip_url
    assert f"/live/{dev.id}/whep" in stream.whep_url
    assert f"/live/{dev.id}" in stream.rtsp_url
    assert f"/live/{dev.id}/index.m3u8" in stream.hls_url

    # Camera device status updated to ONLINE
    updated_dev = device_service.get_device_sync(dev.id)
    assert updated_dev.status == CameraStatus.ONLINE


def test_prevent_duplicate_stream_sessions():
    dev = device_service.register_device_sync(DeviceCreate(
        name="Traffic Cam 2",
        location="Broadway & 47th St",
    ))

    # First session starts
    s1 = stream_service.start_stream_sync(StreamStartRequest(device_id=dev.id))
    assert s1.status == StreamStatus.STARTING

    # Attempting to start another session without force_restart raises DuplicateStreamSessionError
    with pytest.raises(DuplicateStreamSessionError):
        stream_service.start_stream_sync(StreamStartRequest(device_id=dev.id, force_restart=False))

    # Starting with force_restart=True succeeds and supersedes the old session
    s2 = stream_service.start_stream_sync(StreamStartRequest(device_id=dev.id, force_restart=True))
    assert s2.id != s1.id

    # Old session marked as STOPPED
    old_session = stream_service.get_stream_sync(s1.id)
    assert old_session.status == StreamStatus.STOPPED


def test_start_stream_device_not_found():
    with pytest.raises(DeviceNotFoundError):
        stream_service.start_stream_sync(StreamStartRequest(device_id="non-existent-device-id"))


def test_start_stream_device_inactive():
    dev = device_service.register_device_sync(DeviceCreate(
        name="Inactive Cam",
        location="Back Alley",
    ))
    device_service.deactivate_device_sync(dev.id)

    with pytest.raises(DeviceInactiveError):
        stream_service.start_stream_sync(StreamStartRequest(device_id=dev.id))


def test_stop_stream_success():
    dev = device_service.register_device_sync(DeviceCreate(
        name="Traffic Cam 3",
        location="Main & Elm",
    ))

    s = stream_service.start_stream_sync(StreamStartRequest(device_id=dev.id))

    stopped = stream_service.stop_stream_sync(StreamStopRequest(stream_id=s.id, reason="User initiated"))
    assert stopped is not None
    assert stopped.status == StreamStatus.STOPPED
    assert stopped.ended_at is not None
    assert stopped.error_message == "User initiated"

    # Camera device status reset to OFFLINE
    updated_dev = device_service.get_device_sync(dev.id)
    assert updated_dev.status == CameraStatus.OFFLINE


def test_stream_status_update_lifecycle():
    dev = device_service.register_device_sync(DeviceCreate(
        name="Traffic Cam 4",
        location="Highway 101",
    ))

    s = stream_service.start_stream_sync(StreamStartRequest(device_id=dev.id))

    # Transition to LIVE
    live = stream_service.update_status_sync(s.id, StreamStatusUpdate(status=StreamStatus.LIVE))
    assert live.status == StreamStatus.LIVE
    dev_live = device_service.get_device_sync(dev.id)
    assert dev_live.status == CameraStatus.ONLINE

    # Transition to RECONNECTING
    recon = stream_service.update_status_sync(
        s.id,
        StreamStatusUpdate(status=StreamStatus.RECONNECTING, error_message="ICE connection lost"),
    )
    assert recon.status == StreamStatus.RECONNECTING
    assert recon.reconnect_attempts == 1
    dev_recon = device_service.get_device_sync(dev.id)
    assert dev_recon.status == CameraStatus.RECONNECTING

    # Transition to FAILED
    failed = stream_service.update_status_sync(
        s.id,
        StreamStatusUpdate(status=StreamStatus.FAILED, error_message="Network unreachable"),
    )
    assert failed.status == StreamStatus.FAILED
    dev_failed = device_service.get_device_sync(dev.id)
    assert dev_failed.status == CameraStatus.ERROR


def test_stream_heartbeat():
    dev = device_service.register_device_sync(DeviceCreate(
        name="Heartbeat Cam",
        location="South Gate",
    ))

    s = stream_service.start_stream_sync(StreamStartRequest(device_id=dev.id))

    hb = stream_service.record_heartbeat_sync(
        s.id,
        StreamHeartbeat(status=StreamStatus.LIVE, stats={"fps": 30, "bitrate": 1500000}),
    )
    assert hb is not None
    assert hb.stream_metadata["last_stats"]["fps"] == 30
    assert hb.stream_metadata["last_stats"]["bitrate"] == 1500000
