/**
 * Stream Service for Stream Lifecycle and WebRTC WHIP Publishing [M1].
 */
import {
  StreamSession,
  StartStreamPayload,
  StopStreamPayload,
  StreamStatus,
} from '../types/camera.types';

const API_BASE = (((import.meta as any).env && (import.meta as any).env.VITE_API_BASE_URL) || 'http://localhost:8000').replace(/\/+$/, '');

class StreamService {
  /**
   * Start a streaming session for a camera device.
   */
  async startStream(payload: StartStreamPayload): Promise<StreamSession> {
    const res = await fetch(`${API_BASE}/api/streams/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Failed to start stream session');
    }
    return res.json();
  }

  /**
   * Stop an active streaming session.
   */
  async stopStream(payload: StopStreamPayload): Promise<StreamSession> {
    const body = {
      device_id: payload.device_id || payload.deviceId,
      stream_id: payload.stream_id || payload.streamId,
      reason: payload.reason,
    };
    const res = await fetch(`${API_BASE}/api/streams/stop`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Failed to stop stream session');
    }
    return res.json();
  }

  /**
   * Retrieve active stream for a specific device.
   */
  async getDeviceStream(deviceId: string): Promise<StreamSession | null> {
    const res = await fetch(`${API_BASE}/api/streams/device/${deviceId}`);
    if (res.status === 404) {
      return null;
    }
    if (!res.ok) {
      throw new Error(`Failed to fetch device stream (${res.status})`);
    }
    return res.json();
  }

  /**
   * Update stream status on backend.
   */
  async updateStreamStatus(
    streamId: string,
    status: StreamStatus,
    errorMessage?: string
  ): Promise<StreamSession> {
    const res = await fetch(`${API_BASE}/api/streams/${streamId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, error_message: errorMessage }),
    });
    if (!res.ok) {
      throw new Error(`Failed to update stream status (${res.status})`);
    }
    return res.json();
  }

  /**
   * Publish media stream to MediaMTX via WebRTC WHIP.
   * Performs standard SDP offer/answer exchange with MediaMTX WHIP endpoint.
   */
  async publishWHIP(
    whipUrl: string,
    stream: MediaStream,
    onConnectionStateChange?: (state: RTCPeerConnectionState) => void
  ): Promise<{ pc: RTCPeerConnection; stop: () => Promise<void> }> {
    const videoTrack = stream.getVideoTracks()[0];
    if (!videoTrack) {
      throw new Error('No video track available in media stream to publish');
    }

    const pc = new RTCPeerConnection({
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' },
      ],
      bundlePolicy: 'max-bundle',
    });

    if (onConnectionStateChange) {
      pc.onconnectionstatechange = () => {
        onConnectionStateChange(pc.connectionState);
      };
    }

    pc.addTransceiver(videoTrack, {
      direction: 'sendonly',
      streams: [stream],
    });

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    await new Promise<void>((resolve) => {
      if (pc.iceGatheringState === 'complete') {
        resolve();
      } else {
        const timeout = setTimeout(() => {
          pc.removeEventListener('icegatheringstatechange', checkIce);
          resolve();
        }, 1500);

        const checkIce = () => {
          if (pc.iceGatheringState === 'complete') {
            clearTimeout(timeout);
            pc.removeEventListener('icegatheringstatechange', checkIce);
            resolve();
          }
        };
        pc.addEventListener('icegatheringstatechange', checkIce);
      }
    });

    const sdpOffer = pc.localDescription?.sdp;
    if (!sdpOffer) {
      throw new Error('Failed to generate local SDP offer');
    }

    let resourceUrl: string | null = null;
    const response = await fetch(whipUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/sdp',
      },
      body: sdpOffer,
    });

    if (!response.ok) {
      pc.close();
      const errText = await response.text().catch(() => response.statusText);
      throw new Error(`MediaMTX WHIP publish failed (${response.status}): ${errText}`);
    }

    resourceUrl = response.headers.get('Location') || whipUrl;

    const answerSdp = await response.text();
    await pc.setRemoteDescription({
      type: 'answer',
      sdp: answerSdp,
    });

    const stop = async () => {
      try {
        if (resourceUrl) {
          await fetch(resourceUrl, { method: 'DELETE' }).catch(() => { });
        }
      } catch {
        // Ignore deletion network errors during shutdown
      } finally {
        pc.close();
      }
    };

    return { pc, stop };
  }
}

export const streamService = new StreamService();
