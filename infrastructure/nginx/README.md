# NGINX Reverse Proxy Configuration [M1]

This directory contains the production-grade reverse proxy configuration for the Social Empowerment Platform.

## Routing Architecture

```
Client Requests (Port 80)
 │
 ├── /api/                       ──► FastAPI Backend (api:8000)
 ├── /ws/                        ──► FastAPI WebSockets (api:8000/ws/)
 ├── /live/<camera_id>/whip      ──► MediaMTX WebRTC Publish (video-gateway:8889)
 ├── /live/<camera_id>/whep      ──► MediaMTX WebRTC Playback (video-gateway:8889)
 ├── /hls/                       ──► MediaMTX HLS Segments (video-gateway:8888)
 ├── /gateway-api/               ──► MediaMTX Control API (video-gateway:9997/v3/)
 └── /                           ──► React Single-Page Application (web:80)
```

## Streaming Optimizations Applied

1. **Proxy Buffering Disabled (`proxy_buffering off`)**:
   Crucial for WebRTC WHIP/WHEP HTTP signaling and HLS video streaming to ensure sub-second transmission without kernel chunk buffering.
2. **Extended Timeouts (`proxy_read_timeout 86400s`)**:
   Maintains long-lived HTTP and WebSocket connections without premature disconnections.
3. **CORS Handling**:
   Automatically returns pre-flight `OPTIONS 204` responses with headers allowing seamless cross-origin browser streaming.
4. **WebSocket Upgrade Headers**:
   Includes `Upgrade $http_upgrade` and `Connection "upgrade"` to support real-time incident and event pushes.

