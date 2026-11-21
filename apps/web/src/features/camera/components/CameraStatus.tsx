/**
 * Camera Status Badge & WebRTC Stream Health Component [M1].
 */
import React from 'react';
import { CameraStatus as CamStatusType, StreamStatus as StrmStatusType } from '../types/camera.types';

export interface CameraStatusBadgeProps {
  cameraStatus: CamStatusType;
  streamStatus: StrmStatusType;
  reconnectAttempts?: number;
  rtspUrl?: string;
  whipUrl?: string;
}

export const CameraStatusBadge: React.FC<CameraStatusBadgeProps> = ({
  cameraStatus,
  streamStatus,
  reconnectAttempts = 0,
  rtspUrl,
  whipUrl,
}) => {
  const getCameraColor = () => {
    switch (cameraStatus) {
      case 'ONLINE':
        return '#22c55e';
      case 'RECONNECTING':
        return '#f59e0b';
      case 'ERROR':
        return '#ef4444';
      case 'OFFLINE':
      default:
        return '#94a3b8';
    }
  };

  const getStreamColor = () => {
    switch (streamStatus) {
      case 'LIVE':
        return '#ef4444';
      case 'STARTING':
      case 'RECONNECTING':
        return '#f59e0b';
      case 'FAILED':
        return '#b91c1c';
      case 'STOPPED':
      default:
        return '#64748b';
    }
  };

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '12px',
        backgroundColor: '#0f172a',
        padding: '16px',
        borderRadius: '8px',
        border: '1px solid #334155',
      }}
    >
      {/* Device Connection Status */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <span style={{ fontSize: '12px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>
          Device Status
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: getCameraColor(),
            }}
          />
          <strong style={{ color: '#f8fafc', fontSize: '14px' }}>{cameraStatus}</strong>
        </div>
      </div>

      {/* WebRTC Streaming Status */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <span style={{ fontSize: '12px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>
          Stream Status
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: getStreamColor(),
            }}
          />
          <strong style={{ color: '#f8fafc', fontSize: '14px' }}>{streamStatus}</strong>
          {reconnectAttempts > 0 && (
            <span style={{ fontSize: '12px', color: '#f59e0b' }}>
              (Retry #{reconnectAttempts})
            </span>
          )}
        </div>
      </div>

      {/* Gateway Ingest (WHIP) Details */}
      {whipUrl && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <span style={{ fontSize: '12px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>
            WHIP Endpoint (M1)
          </span>
          <span
            style={{
              fontSize: '11px',
              fontFamily: 'monospace',
              color: '#38bdf8',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
            title={whipUrl}
          >
            {whipUrl}
          </span>
        </div>
      )}

      {/* AI RTSP Stream Endpoint */}
      {rtspUrl && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <span style={{ fontSize: '12px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>
            AI Worker Feed (M2)
          </span>
          <span
            style={{
              fontSize: '11px',
              fontFamily: 'monospace',
              color: '#4ade80',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
            title={rtspUrl}
          >
            {rtspUrl}
          </span>
        </div>
      )}
    </div>
  );
};
