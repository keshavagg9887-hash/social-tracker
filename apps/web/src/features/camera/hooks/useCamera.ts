/**
 * Custom React hook for Browser MediaDevices camera access [M1].
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { CameraDeviceInfo } from '../types/camera.types';
import { cameraService } from '../services/cameraService';

export type PermissionState = 'prompt' | 'granted' | 'denied' | 'error';

export interface UseCameraResult {
  stream: MediaStream | null;
  devices: CameraDeviceInfo[];
  selectedDeviceId: string;
  permission: PermissionState;
  errorMessage: string | null;
  isLoading: boolean;
  selectDevice: (deviceId: string) => Promise<void>;
  requestPermission: () => Promise<void>;
  refreshDevices: () => Promise<void>;
  stopCamera: () => void;
}

export function useCamera(): UseCameraResult {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [devices, setDevices] = useState<CameraDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');
  const [permission, setPermission] = useState<PermissionState>('prompt');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const streamRef = useRef<MediaStream | null>(null);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      setStream(null);
    }
  }, []);

  const refreshDevices = useCallback(async () => {
    try {
      const cams = await cameraService.getAvailableWebcams();
      setDevices(cams);
      if (cams.length > 0 && !selectedDeviceId) {
        setSelectedDeviceId(cams[0].deviceId);
      }
    } catch (err: any) {
      console.warn('Unable to enumerate camera devices:', err);
    }
  }, [selectedDeviceId]);

  const startStream = useCallback(
    async (deviceId?: string) => {
      setIsLoading(true);
      setErrorMessage(null);

      // Stop any existing tracks
      stopCamera();

      try {
        const newStream = await cameraService.getMediaStream(deviceId);
        streamRef.current = newStream;
        setStream(newStream);
        setPermission('granted');

        // Detect track ending (e.g., unplugged USB webcam)
        newStream.getVideoTracks().forEach((track) => {
          track.onended = () => {
            setErrorMessage('Camera disconnected or in use by another application.');
            stopCamera();
          };
        });

        // Refresh devices to get proper labels after permission is granted
        await refreshDevices();
      } catch (err: any) {
        let msg = 'Failed to access camera.';
        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
          setPermission('denied');
          msg = 'Camera permission denied. Please allow camera access in your browser settings.';
        } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
          setPermission('error');
          msg = 'No camera device found on this system.';
        } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
          setPermission('error');
          msg = 'Camera hardware is currently in use by another application or OS service.';
        } else if (err.name === 'OverconstrainedError') {
          setPermission('error');
          msg = 'Camera does not satisfy the requested resolution constraints.';
        } else {
          setPermission('error');
          msg = err.message || 'Unknown camera hardware error occurred.';
        }
        setErrorMessage(msg);
        stopCamera();
      } finally {
        setIsLoading(false);
      }
    },
    [refreshDevices, stopCamera]
  );

  const selectDevice = useCallback(
    async (deviceId: string) => {
      setSelectedDeviceId(deviceId);
      await startStream(deviceId);
    },
    [startStream]
  );

  const requestPermission = useCallback(async () => {
    await startStream(selectedDeviceId || undefined);
  }, [selectedDeviceId, startStream]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  return {
    stream,
    devices,
    selectedDeviceId,
    permission,
    errorMessage,
    isLoading,
    selectDevice,
    requestPermission,
    refreshDevices,
    stopCamera,
  };
}

