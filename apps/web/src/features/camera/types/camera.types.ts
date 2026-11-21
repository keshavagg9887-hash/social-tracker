/**
 * Types and interfaces for Camera and WebRTC Streaming [M1].
 */

export type CameraStatus = 'ONLINE' | 'OFFLINE' | 'RECONNECTING' | 'ERROR';

export type StreamStatus = 'STOPPED' | 'STARTING' | 'LIVE' | 'RECONNECTING' | 'FAILED';

export interface CameraDevice {
  id: string;
  name: string;
  location: string;
  latitude: number | null;
  longitude: number | null;
  status: CameraStatus;
  is_active: boolean;
  device_metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  last_seen_at: string | null;
}

export interface RegisterCameraPayload {
  name: string;
  location: string;
  latitude?: number | null;
  longitude?: number | null;
  device_metadata?: Record<string, any>;
}

export interface UpdateCameraPayload {
  name?: string;
  location?: string;
  latitude?: number | null;
  longitude?: number | null;
  status?: CameraStatus;
  is_active?: boolean;
  device_metadata?: Record<string, any>;
}

export interface StreamSession {
  id: string;
  device_id: string;
  status: StreamStatus;
  stream_path: string;
  whip_url: string;
  whep_url: string;
  rtsp_url: string;
  hls_url: string;
  started_at: string;
  ended_at?: string | null;
  error_message?: string | null;
  reconnect_attempts: number;
  stream_metadata?: Record<string, any>;
}

export interface StartStreamPayload {
  device_id: string;
  force_restart?: boolean;
  stream_metadata?: Record<string, any>;
}

export interface StopStreamPayload {
  device_id?: string;
  deviceId?: string;
  stream_id?: string;
  streamId?: string;
  reason?: string;
}

export interface CameraDeviceInfo {
  deviceId: string;
  label: string;
  groupId?: string;
}

export interface CameraLocationState {
  name: string;
  location: string;
  latitude: number | null;
  longitude: number | null;
}

export interface WebRTCConnectionStats {
  bytesSent: number;
  packetsSent: number;
  currentRoundTripTime?: number;
  frameWidth?: number;
  frameHeight?: number;
  framesPerSecond?: number;
}
