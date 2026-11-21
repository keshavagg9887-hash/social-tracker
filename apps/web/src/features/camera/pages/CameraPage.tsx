/**
 * Complete Camera Client Page Component [M1].
 * Integrated camera registration, webcam preview, and real-time WebRTC streaming.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { CameraDevice, RegisterCameraPayload } from '../types/camera.types';
import { cameraService } from '../services/cameraService';
import { useCamera } from '../hooks/useCamera';
import { useWebRTC } from '../hooks/useWebRTC';
import { CameraPreview } from '../components/CameraPreview';
import { CameraSelector } from '../components/CameraSelector';
import { CameraControls } from '../components/CameraControls';
import { CameraStatusBadge } from '../components/CameraStatus';
import { CameraLocationForm } from '../components/CameraLocationForm';
import { CameraList } from '../components/CameraList';

export const CameraPage: React.FC = () => {
  const [cameras, setCameras] = useState<CameraDevice[]>([]);
  const [selectedCamera, setSelectedCamera] = useState<CameraDevice | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isFetchingCameras, setIsFetchingCameras] = useState(false);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  // Browser webcam hook
  const {
    stream,
    devices,
    selectedDeviceId,
    errorMessage: cameraError,
    isLoading: cameraLoading,
    selectDevice,
    requestPermission,
    refreshDevices,
    stopCamera,
  } = useCamera();

  // WebRTC Live Streaming hook
  const {
    streamSession,
    streamStatus,
    reconnectAttempts,
    errorMessage: streamError,
    startStreaming,
    stopStreaming,
  } = useWebRTC({
    deviceId: selectedCamera?.id || null,
    mediaStream: stream,
  });

  const loadRegisteredCameras = useCallback(async () => {
    setIsFetchingCameras(true);
    try {
      const list = await cameraService.listCameras();
      setCameras(list);
      if (!selectedCamera && list.length > 0) {
        setSelectedCamera(list[0]);
      }
    } catch (err: any) {
      console.warn('Could not load camera list:', err);
    } finally {
      setIsFetchingCameras(false);
    }
  }, [selectedCamera]);

  useEffect(() => {
    loadRegisteredCameras();
  }, [loadRegisteredCameras]);

  const handleRegisterCamera = async (payload: RegisterCameraPayload) => {
    setIsSubmitting(true);
    try {
      const created = await cameraService.registerCamera(payload);
      setCameras((prev) => [created, ...prev]);
      setSelectedCamera(created);
      setActionNotice(`Successfully registered camera "${created.name}"!`);
      setTimeout(() => setActionNotice(null), 4000);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteCamera = async (id: string) => {
    try {
      await cameraService.deleteCamera(id, true);
      setCameras((prev) => prev.filter((c) => c.id !== id));
      if (selectedCamera?.id === id) {
        setSelectedCamera(null);
      }
      setActionNotice('Camera removed successfully.');
      setTimeout(() => setActionNotice(null), 3000);
    } catch (err: any) {
      alert(`Failed to delete camera: ${err.message}`);
    }
  };

  const handleSelectCamera = (cam: CameraDevice) => {
    if (streamStatus === 'LIVE' || streamStatus === 'STARTING') {
      alert('Please stop the current live stream before switching active camera device.');
      return;
    }
    setSelectedCamera(cam);
  };

  const currentCamStatus = streamStatus === 'LIVE'
    ? 'ONLINE'
    : streamStatus === 'RECONNECTING'
    ? 'RECONNECTING'
    : streamStatus === 'FAILED'
    ? 'ERROR'
    : selectedCamera?.status || 'OFFLINE';

  return (
    <div
      style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '24px 16px',
        fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        color: '#f8fafc',
      }}
    >
      {/* Header */}
      <header style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <span style={{ fontSize: '28px' }}>📹</span>
          <div>
            <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 700, color: '#ffffff' }}>
              Camera Monitoring Client
            </h1>
            <p style={{ margin: 0, fontSize: '14px', color: '#94a3b8' }}>
              Register local webcams, preview hardware feeds, and stream real-time WebRTC video to MediaMTX for AI detection.
            </p>
          </div>
        </div>

        {actionNotice && (
          <div
            style={{
              marginTop: '12px',
              padding: '10px 16px',
              backgroundColor: 'rgba(34, 197, 94, 0.15)',
              border: '1px solid #22c55e',
              borderRadius: '6px',
              color: '#4ade80',
              fontSize: '13px',
              fontWeight: 600,
            }}
          >
            ✓ {actionNotice}
          </div>
        )}
      </header>

      {/* Main Grid: Stream Preview & Controls (Left) vs Registration & Device List (Right) */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1.3fr) minmax(0, 1fr)',
          gap: '24px',
          alignItems: 'start',
        }}
      >
        {/* Left Column: Video Feed & Live Controls */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Live Video Preview */}
          <CameraPreview
            stream={stream}
            cameraStatus={currentCamStatus}
            streamStatus={streamStatus}
            isLoading={cameraLoading}
            errorMessage={cameraError || streamError}
            onRequestPermission={requestPermission}
          />

          {/* Webcam Selector Dropdown */}
          <CameraSelector
            devices={devices}
            selectedDeviceId={selectedDeviceId}
            onSelectDevice={selectDevice}
            onRefresh={refreshDevices}
            disabled={streamStatus === 'LIVE' || streamStatus === 'STARTING'}
          />

          {/* Action Controls: Start/Stop Preview & Streaming */}
          <CameraControls
            hasPreview={!!stream}
            streamStatus={streamStatus}
            selectedCameraId={selectedCamera?.id || null}
            onStartMonitoring={startStreaming}
            onStopMonitoring={stopStreaming}
            onRequestPreview={requestPermission}
            onStopPreview={stopCamera}
          />

          {/* Stream & Gateway Telemetry */}
          <CameraStatusBadge
            cameraStatus={currentCamStatus}
            streamStatus={streamStatus}
            reconnectAttempts={reconnectAttempts}
            rtspUrl={streamSession?.rtsp_url}
            whipUrl={streamSession?.whip_url}
          />
        </div>

        {/* Right Column: Registration & List of Cameras */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <CameraLocationForm
            onRegister={handleRegisterCamera}
            isSubmitting={isSubmitting}
          />

          <CameraList
            cameras={cameras}
            selectedCameraId={selectedCamera?.id || null}
            onSelectCamera={handleSelectCamera}
            onDeleteCamera={handleDeleteCamera}
            isLoading={isFetchingCameras}
          />
        </div>
      </div>
    </div>
  );
};
