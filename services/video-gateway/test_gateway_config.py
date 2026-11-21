"""Test validation for MediaMTX Video Gateway configuration [M1]."""
import os
from pathlib import Path


def test_mediamtx_yaml_structure():
    """Verify mediamtx.yml exists and contains all required protocol ports and WebRTC configs."""
    gateway_dir = Path(__file__).parent
    config_file = gateway_dir / "mediamtx.yml"
    assert config_file.exists(), "mediamtx.yml must exist in services/video-gateway/"

    content = config_file.read_text(encoding="utf-8")

    # Assert essential streaming protocol ports
    assert "rtspAddress: :8554" in content, "RTSP port 8554 must be configured for AI worker"
    assert "webrtcAddress: :8889" in content, "WebRTC port 8889 must be configured for WHIP/WHEP"
    assert "hlsAddress: :8888" in content, "HLS port 8888 must be configured"
    assert "apiAddress: :9997" in content, "Control API port 9997 must be configured"

    # Assert WebRTC critical configurations
    assert "webrtcAllowCrossOrigin: yes" in content, "CORS must be enabled for browser WHIP/WHEP"
    assert "webrtcICEServers2:" in content, "STUN servers must be declared for WebRTC NAT traversal"

    # Assert paths
    assert "paths:" in content
    assert "~^live/(?P<name>.+):" in content or "live/*:" in content or "all:" in content


def test_dockerfile_exists():
    """Verify Dockerfile exists for MediaMTX gateway."""
    dockerfile = Path(__file__).parent / "Dockerfile"
    assert dockerfile.exists(), "Dockerfile must exist in services/video-gateway/"
    content = dockerfile.read_text(encoding="utf-8")
    assert "mediamtx" in content.lower()

