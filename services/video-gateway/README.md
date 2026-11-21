# Video Gateway Service [M1]

The Video Gateway is powered by **MediaMTX**, a zero-dependency, high-performance real-time media server. It acts as the central media hub for the Social Empowerment Platform, bridging browser camera inputs with AI detection workers and operator dashboards.

## Architecture Overview

```
[Browser Camera (M1)]
        │ WebRTC (WHIP)
        ▼
[MediaMTX Gateway (M1)]  ─── RTSP (TCP/UDP) ───►  [AI Worker: YOLO/PyTorch (M2)]
        │ WebRTC (WHEP) / HLS
        ▼
[Handler Dashboard (M4)]
```

## Transport Protocols & Ports

| Protocol | Port | Direction | Consumer / Producer | Purpose |
|----------|------|-----------|---------------------|---------|
| **WebRTC WHIP** | `8889` | Ingest (Publish) | Browser Camera Client (M1) | Sub-second ultra-low latency webcam ingest via HTTP SDP exchange (`/live/<camera_id>/whip`) |
| **WebRTC WHEP** | `8889` | Egress (Playback) | Handler Dashboard (M4) | Real-time monitoring playback (`/live/<camera_id>/whep`) |
| **RTSP** | `8554` | Egress (Playback) | AI Worker (M2) | Frame extraction and computer vision pipeline (`rtsp://video-gateway:8554/live/<camera_id>`) |
| **HLS** | `8888` | Egress (Playback) | Web fallback (M4) | Safari / Mobile fallback video playback (`http://localhost:8888/live/<camera_id>/index.m3u8`) |
| **Control API**| `9997` | Admin / Metrics | Backend / Health checks | MediaMTX REST API v3 for active path and client inspection (`http://localhost:9997/v3/paths/list`) |

## WebRTC WHIP Ingestion Flow

1. Browser initiates camera capture via `navigator.mediaDevices.getUserMedia`.
2. Browser creates an `RTCPeerConnection` and adds video track.
3. Browser creates an SDP Offer with sendonly media direction.
4. Browser sends an HTTP POST request containing the SDP offer to:
   `http://<gateway_host>:8889/live/<camera_id>/whip` with `Content-Type: application/sdp`.
5. MediaMTX allocates a session, sets remote description, generates an SDP Answer, and responds with HTTP `201 Created` and `Content-Type: application/sdp`.
6. Browser sets the received SDP Answer as local description. WebRTC connection state transitions to `connected`.
7. Video feed is immediately transcoded / remuxed in memory and exposed over RTSP for M2 and WHEP for M4.

## MediaMTX Configuration (`mediamtx.yml`)

- **CORS enabled**: `webrtcAllowCrossOrigin: yes` allows browser-based WHIP and WHEP requests without cross-origin blocks.
- **Public STUN servers**: Configured with Google STUN servers for NAT traversal.
- **Dynamic paths**: Supports dynamic path matching `live/<camera_id>`.

## Running Locally

Using Docker:
```bash
docker run --rm -it \
  -p 8554:8554 \
  -p 1935:1935 \
  -p 8888:8888 \
  -p 8889:8889 \
  -p 9997:9997 \
  -v $(pwd)/mediamtx.yml:/mediamtx.yml \
  bluenviron/mediamtx:latest
```
