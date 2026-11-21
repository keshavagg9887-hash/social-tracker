/**
 * Camera Controls Component [M1].
 * Start / Stop preview and WebRTC streaming controls with duplicate prevention.
 */
import React from 'react';
import { StreamStatus } from '../types/camera.types';

interface CameraControlsProps {
  hasPreview: boolean;
  streamStatus: StreamStatus;
  selectedCameraId: string | null;
  onStartMonitoring: () => void;
  onStopMonitoring: () => void;
  onRequestPreview: () => void;
  onStopPreview: () => void;
  disabled?: boolean;
}

export const CameraControls: React.FC<CameraControlsProps> = ({
  hasPreview,
  streamStatus,
  selectedCameraId,
  onStartMonitoring,
  onStopMonitoring,
  onRequestPreview,
  onStopPreview,
  disabled = false,
}) => {
  const isStreaming = streamStatus === 'LIVE' || streamStatus === 'STARTING';
  const isStarting = streamStatus === 'STARTING';

  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '12px',
        alignItems: 'center',
        padding: '16px',
        backgroundColor: '#1e293b',
        borderRadius: '8px',
        border: '1px solid #334155',
      }}
    >
      {/* Preview Toggle */}
      {!hasPreview ? (
        <button
          onClick={onRequestPreview}
          disabled={disabled || isStreaming}
          style={{
            backgroundColor: '#0284c7',
            color: '#ffffff',
            border: 'none',
            padding: '10px 18px',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: 600,
            cursor: disabled || isStreaming ? 'not-allowed' : 'pointer',
            opacity: disabled || isStreaming ? 0.6 : 1,
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <span>👁️</span> Turn On Camera Preview
        </button>
      ) : (
        <button
          onClick={onStopPreview}
          disabled={disabled || isStreaming}
          style={{
            backgroundColor: '#475569',
            color: '#ffffff',
            border: 'none',
            padding: '10px 18px',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: 600,
            cursor: disabled || isStreaming ? 'not-allowed' : 'pointer',
            opacity: disabled || isStreaming ? 0.6 : 1,
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <span>⏹️</span> Turn Off Preview
        </button>
      )}

      {/* WebRTC Live Stream Toggle */}
      {!isStreaming ? (
        <button
          onClick={onStartMonitoring}
          disabled={disabled || !hasPreview || !selectedCameraId}
          style={{
            backgroundColor: '#16a34a',
            color: '#ffffff',
            border: 'none',
            padding: '10px 22px',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: 700,
            cursor: disabled || !hasPreview || !selectedCameraId ? 'not-allowed' : 'pointer',
            opacity: disabled || !hasPreview || !selectedCameraId ? 0.5 : 1,
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            boxShadow: hasPreview && selectedCameraId ? '0 4px 14px rgba(22, 163, 74, 0.4)' : 'none',
          }}
        >
          <span>📡</span> Start Monitoring (Publish WebRTC)
        </button>
      ) : (
        <button
          onClick={onStopMonitoring}
          disabled={disabled}
          style={{
            backgroundColor: '#dc2626',
            color: '#ffffff',
            border: 'none',
            padding: '10px 22px',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: 700,
            cursor: disabled ? 'not-allowed' : 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            boxShadow: '0 4px 14px rgba(220, 38, 38, 0.4)',
          }}
        >
          <span>⏹️</span> {isStarting ? 'Aborting...' : 'Stop Monitoring'}
        </button>
      )}

      {!selectedCameraId && hasPreview && (
        <span style={{ color: '#f59e0b', fontSize: '13px', marginLeft: 'auto' }}>
          ⚠️ Select or register a camera device below before streaming.
        </span>
      )}
    </div>
  );
};

