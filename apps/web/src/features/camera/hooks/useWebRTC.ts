/**
 * Custom React hook for WebRTC Live Streaming lifecycle [M1].
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import { StreamSession, StreamStatus } from '../types/camera.types';
import { streamService } from '../services/streamService';

export interface UseWebRTCProps {
  deviceId: string | null;
  mediaStream: MediaStream | null;
  onStatusChange?: (status: StreamStatus) => void;
}

export interface UseWebRTCResult {
  streamSession: StreamSession | null;
  streamStatus: StreamStatus;
  isStreaming: boolean;
  reconnectAttempts: number;
  errorMessage: string | null;
  startStreaming: () => Promise<void>;
  stopStreaming: () => Promise<void>;
}

export function useWebRTC({ deviceId, mediaStream, onStatusChange }: UseWebRTCProps): UseWebRTCResult {
  const [streamSession, setStreamSession] = useState<StreamSession | null>(null);
  const [streamStatus, setStreamStatus] = useState<StreamStatus>('STOPPED');
  const [reconnectAttempts, setReconnectAttempts] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const stopWhipRef = useRef<(() => Promise<void>) | null>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);
  const heartbeatIntervalRef = useRef<any>(null);

  const updateStatus = useCallback(
    (newStatus: StreamStatus, errorMsg?: string) => {
      setStreamStatus(newStatus);
      if (errorMsg) {
        setErrorMessage(errorMsg);
      }
      if (onStatusChange) {
        onStatusChange(newStatus);
      }
    },
    [onStatusChange]
  );

  const stopStreaming = useCallback(async () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }

    if (stopWhipRef.current) {
      await stopWhipRef.current().catch(() => {});
      stopWhipRef.current = null;
    }

    if (pcRef.current) {
      pcRef.current.close();
      pcRef.current = null;
    }

    if (deviceId) {
      try {
        await streamService.stopStream({ deviceId });
      } catch (err) {
        console.warn('Backend stream stop call failed:', err);
      }
    }

    setStreamSession(null);
    setReconnectAttempts(0);
    setErrorMessage(null);
    updateStatus('STOPPED');
  }, [deviceId, updateStatus]);

  const publishToMediaMTX = useCallback(
    async (session: StreamSession, stream: MediaStream): Promise<void> => {
      try {
        const { pc, stop } = await streamService.publishWHIP(
          session.whip_url,
          stream,
          (state) => {
            if (state === 'connected') {
              updateStatus('LIVE');
              setErrorMessage(null);
              setReconnectAttempts(0);
              streamService.updateStreamStatus(session.id, 'LIVE').catch(() => {});
            } else if (state === 'disconnected' || state === 'failed') {
              handleDisconnection(session, stream);
            }
          }
        );

        pcRef.current = pc;
        stopWhipRef.current = stop;

        // Start heartbeat keepalive
        heartbeatIntervalRef.current = setInterval(() => {
          streamService.updateStreamStatus(session.id, 'LIVE').catch(() => {});
        }, 15000);
      } catch (err: any) {
        throw new Error(`WebRTC negotiation failed: ${err.message}`);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [updateStatus]
  );

  const handleDisconnection = useCallback(
    async (session: StreamSession, stream: MediaStream) => {
      updateStatus('RECONNECTING', 'Connection lost. Attempting auto-reconnect...');

      if (reconnectAttempts < 3) {
        const nextAttempt = reconnectAttempts + 1;
        setReconnectAttempts(nextAttempt);
        const delay = Math.min(1000 * Math.pow(2, nextAttempt), 8000);

        reconnectTimeoutRef.current = setTimeout(async () => {
          try {
            if (stopWhipRef.current) {
              await stopWhipRef.current().catch(() => {});
            }
            await publishToMediaMTX(session, stream);
          } catch (reconnectErr: any) {
            console.error('Reconnect attempt failed:', reconnectErr);
            handleDisconnection(session, stream);
          }
        }, delay);
      } else {
        updateStatus('FAILED', 'Max reconnection attempts exceeded. Stream halted.');
        await streamService.updateStreamStatus(session.id, 'FAILED', 'Max retries exceeded').catch(() => {});
      }
    },
    [publishToMediaMTX, reconnectAttempts, updateStatus]
  );

  const startStreaming = useCallback(async () => {
    if (!deviceId) {
      setErrorMessage('No camera device selected for streaming.');
      return;
    }
    if (!mediaStream) {
      setErrorMessage('No active camera preview found. Please enable camera first.');
      return;
    }
    if (streamStatus === 'LIVE' || streamStatus === 'STARTING') {
      return; // Prevent duplicate sessions
    }

    setErrorMessage(null);
    updateStatus('STARTING');

    try {
      // 1. Tell backend to start stream and get MediaMTX endpoints
      const session = await streamService.startStream({
        device_id: deviceId,
        force_restart: true,
      });
      setStreamSession(session);

      // 2. Publish media stream to MediaMTX WHIP endpoint
      await publishToMediaMTX(session, mediaStream);
    } catch (err: any) {
      updateStatus('FAILED', err.message || 'Failed to initialize live stream');
      if (deviceId) {
        await streamService.stopStream({ deviceId }).catch(() => {});
      }
    }
  }, [deviceId, mediaStream, streamStatus, updateStatus, publishToMediaMTX]);

  // Cleanup on unmount or device change
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }
      if (stopWhipRef.current) {
        stopWhipRef.current().catch(() => {});
      }
      if (pcRef.current) {
        pcRef.current.close();
      }
    };
  }, []);

  return {
    streamSession,
    streamStatus,
    isStreaming: streamStatus === 'LIVE' || streamStatus === 'STARTING',
    reconnectAttempts,
    errorMessage,
    startStreaming,
    stopStreaming,
  };
}

