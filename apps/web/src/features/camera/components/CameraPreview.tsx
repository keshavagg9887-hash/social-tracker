/**
 * Camera Preview Component [M1].
 * Displays live webcam video feed with status overlays and permission states.
 */
import React, { useEffect, useRef } from 'react';
import { CameraStatus, StreamStatus } from '../types/camera.types';

interface CameraPreviewProps {
  stream: MediaStream | null;
  cameraStatus: CameraStatus;
  streamStatus: StreamStatus;
  isLoading?: boolean;
  errorMessage?: string | null;
  onRequestPermission?: () => void;
}

export const CameraPreview: React.FC<CameraPreviewProps> = ({
  stream,
  cameraStatus,
  streamStatus,
  isLoading = false,
  errorMessage = null,
  onRequestPermission,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    } else if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }, [stream]);

  const isLive = streamStatus === 'LIVE';

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        aspectRatio: '16/9',
        backgroundColor: '#0f172a',
        borderRadius: '12px',
        overflow: 'hidden',
        boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.4)',
        border: isLive ? '2px solid #ef4444' : '1px solid #334155',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {/* Live Video Feed */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          display: stream ? 'block' : 'none',
        }}
      />

      {/* Stream Status Overlay Badge */}
      <div
        style={{
          position: 'absolute',
          top: '16px',
          left: '16px',
          display: 'flex',
          gap: '8px',
          zIndex: 10,
        }}
      >
        {isLive && (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '9999px',
              backgroundColor: '#dc2626',
              color: '#ffffff',
              fontSize: '12px',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              animation: 'pulse 2s infinite',
            }}
          >
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: '#ffffff',
              }}
            />
            LIVE ON AIR
          </span>
        )}

        <span
          style={{
            padding: '4px 10px',
            borderRadius: '9999px',
            backgroundColor: 'rgba(15, 23, 42, 0.8)',
            backdropFilter: 'blur(4px)',
            color: '#94a3b8',
            fontSize: '12px',
            fontWeight: 600,
            border: '1px solid #334155',
          }}
        >
          {cameraStatus}
        </span>
      </div>

      {/* Placeholder / Permission State */}
      {!stream && (
        <div
          style={{
            textAlign: 'center',
            padding: '2rem',
            maxWidth: '420px',
            color: '#94a3b8',
            zIndex: 5,
          }}
        >
          {isLoading ? (
            <div>
              <div
                style={{
                  width: '40px',
                  height: '40px',
                  border: '3px solid #334155',
                  borderTopColor: '#38bdf8',
                  borderRadius: '50%',
                  margin: '0 auto 16px',
                  animation: 'spin 1s linear infinite',
                }}
              />
              <p style={{ fontWeight: 500 }}>Accessing camera hardware...</p>
            </div>
          ) : errorMessage ? (
            <div>
              <div
                style={{
                  width: '48px',
                  height: '48px',
                  margin: '0 auto 12px',
                  borderRadius: '50%',
                  backgroundColor: 'rgba(239, 68, 68, 0.2)',
                  color: '#ef4444',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '24px',
                }}
              >
                ⚠️
              </div>
              <h4 style={{ color: '#f87171', margin: '0 0 8px 0', fontSize: '16px' }}>
                Camera Hardware Error
              </h4>
              <p style={{ fontSize: '13px', lineHeight: '1.5', margin: '0 0 16px 0' }}>
                {errorMessage}
              </p>
              {onRequestPermission && (
                <button
                  onClick={onRequestPermission}
                  style={{
                    backgroundColor: '#0284c7',
                    color: '#ffffff',
                    border: 'none',
                    padding: '8px 16px',
                    borderRadius: '6px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    fontSize: '13px',
                  }}
                >
                  Retry Camera Access
                </button>
              )}
            </div>
          ) : (
            <div>
              <div
                style={{
                  width: '56px',
                  height: '56px',
                  margin: '0 auto 16px',
                  borderRadius: '50%',
                  backgroundColor: '#1e293b',
                  color: '#64748b',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '28px',
                }}
              >
                📹
              </div>
              <h3 style={{ color: '#f1f5f9', margin: '0 0 8px 0', fontSize: '18px' }}>
                Webcam Standby
              </h3>
              <p style={{ fontSize: '13px', lineHeight: '1.5', margin: '0 0 20px 0' }}>
                Grant browser camera permission to preview and start streaming your local webcam to the
                AI detection pipeline.
              </p>
              {onRequestPermission && (
                <button
                  onClick={onRequestPermission}
                  style={{
                    backgroundColor: '#0284c7',
                    color: '#ffffff',
                    border: 'none',
                    padding: '10px 20px',
                    borderRadius: '8px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    fontSize: '14px',
                    boxShadow: '0 4px 12px rgba(2, 132, 199, 0.4)',
                  }}
                >
                  Enable Camera Preview
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

