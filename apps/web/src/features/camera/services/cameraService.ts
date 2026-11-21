/**
 * Camera Service for Device Management and Browser MediaDevices [M1].
 */
import {
  CameraDevice,
  RegisterCameraPayload,
  UpdateCameraPayload,
  CameraDeviceInfo,
  CameraStatus,
} from '../types/camera.types';

const API_BASE = (((import.meta as any).env && (import.meta as any).env.VITE_API_BASE_URL) || 'http://localhost:8000').replace(/\/+$/, '');

class CameraService {
  /**
   * Register a new camera device with backend API.
   */
  async registerCamera(payload: RegisterCameraPayload): Promise<CameraDevice> {
    const res = await fetch(`${API_BASE}/api/devices/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Failed to register camera');
    }
    return res.json();
  }

  /**
   * Fetch all registered camera devices.
   */
  async listCameras(): Promise<CameraDevice[]> {
    const res = await fetch(`${API_BASE}/api/devices/`);
    if (!res.ok) {
      throw new Error(`Failed to list cameras (${res.status})`);
    }
    return res.json();
  }

  /**
   * Fetch single camera details by ID.
   */
  async getCamera(deviceId: string): Promise<CameraDevice> {
    const res = await fetch(`${API_BASE}/api/devices/${deviceId}`);
    if (!res.ok) {
      throw new Error(`Camera ${deviceId} not found`);
    }
    return res.json();
  }

  /**
   * Update camera details or status.
   */
  async updateCamera(deviceId: string, payload: UpdateCameraPayload): Promise<CameraDevice> {
    const res = await fetch(`${API_BASE}/api/devices/${deviceId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new Error(`Failed to update camera ${deviceId}`);
    }
    return res.json();
  }

  /**
   * Deactivate or delete a camera device.
   */
  async deleteCamera(deviceId: string, hardDelete: boolean = false): Promise<CameraDevice> {
    const res = await fetch(`${API_BASE}/api/devices/${deviceId}?hard_delete=${hardDelete}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      throw new Error(`Failed to delete camera ${deviceId}`);
    }
    return res.json();
  }

  /**
   * Send heartbeat to keep camera status current.
   */
  async sendHeartbeat(deviceId: string, status: CameraStatus): Promise<CameraDevice> {
    const res = await fetch(`${API_BASE}/api/devices/${deviceId}/heartbeat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    });
    if (!res.ok) {
      throw new Error(`Heartbeat failed for camera ${deviceId}`);
    }
    return res.json();
  }

  /**
   * Enumerate available video input devices (webcams).
   */
  async getAvailableWebcams(): Promise<CameraDeviceInfo[]> {
    if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
      throw new Error('MediaDevices API not supported in this browser environment');
    }
    const devices = await navigator.mediaDevices.enumerateDevices();
    const videoDevices = devices.filter((d) => d.kind === 'videoinput');

    return videoDevices.map((d, index) => ({
      deviceId: d.deviceId,
      label: d.label || `Camera ${index + 1}`,
      groupId: d.groupId,
    }));
  }

  /**
   * Acquire user media stream for a specific video device.
   * Audio is strictly disabled by default.
   */
  async getMediaStream(deviceId?: string): Promise<MediaStream> {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error('Browser does not support camera capture via getUserMedia');
    }

    const constraints: MediaStreamConstraints = {
      video: deviceId ? { deviceId: { exact: deviceId } } : { width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false, // Strict requirement: audio disabled by default
    };

    return navigator.mediaDevices.getUserMedia(constraints);
  }

  /**
   * Helper to query current GPS coordinates via HTML5 Geolocation.
   */
  async getCurrentLocation(): Promise<{ latitude: number; longitude: number }> {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation is not supported by your browser'));
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: parseFloat(position.coords.latitude.toFixed(6)),
            longitude: parseFloat(position.coords.longitude.toFixed(6)),
          });
        },
        (error) => {
          reject(new Error(error.message || 'Unable to retrieve location coordinates'));
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
      );
    });
  }
}

export const cameraService = new CameraService();
