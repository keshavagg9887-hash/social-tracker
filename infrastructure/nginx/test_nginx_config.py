"""Test validation for NGINX reverse proxy configuration [M1]."""
from pathlib import Path
import re


def test_nginx_conf_structure():
    """Verify infrastructure/nginx/nginx.conf routes and proxy configurations."""
    nginx_dir = Path(__file__).parent
    conf_file = nginx_dir / "nginx.conf"
    assert conf_file.exists(), "nginx.conf must exist in infrastructure/nginx/"

    content = conf_file.read_text(encoding="utf-8")

    # 1. Upstream declarations
    assert "upstream api_backend" in content
    assert "server api:8000;" in content
    assert "upstream video_gateway_webrtc" in content
    assert "server video-gateway:8889;" in content
    assert "upstream video_gateway_hls" in content
    assert "server video-gateway:8888;" in content

    # 2. WebRTC WHIP / WHEP location
    assert "/live/" in content
    assert "proxy_pass http://video_gateway_webrtc" in content
    assert "proxy_buffering off;" in content

    # 3. WebSocket upgrade handling
    assert "proxy_set_header Upgrade $http_upgrade;" in content
    assert "proxy_set_header Connection \"upgrade\";" in content

    # 4. API proxy
    assert "location /api/" in content
    assert "proxy_pass http://api_backend/;" in content

