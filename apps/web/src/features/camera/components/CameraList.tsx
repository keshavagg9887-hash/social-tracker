/**
 * Registered Camera Devices List Component [M1].
 * Displays all registered cameras with their status, coordinates, and selection controls.
 */
import React from 'react';
import { CameraDevice } from '../types/camera.types';

interface CameraListProps {
  cameras: CameraDevice[];
  selectedCameraId: string | null;
  onSelectCamera: (camera: CameraDevice) => void;
  onDeleteCamera: (cameraId: string) => void;
  isLoading?: boolean;
}

export const CameraList: React.FC<CameraListProps> = ({
  cameras,
  selectedCameraId,
  onSelectCamera,
  onDeleteCamera,
  isLoading = false,
}) => {
  return (
    <div
      style={{
        backgroundColor: '#1e293b',
        padding: '20px',
        borderRadius: '8px',
        border: '1px solid #334155',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ margin: 0, color: '#f1f5f9', fontSize: '16px' }}>
          Registered Cameras ({cameras.length})
        </h3>
        {isLoading && <span style={{ color: '#38bdf8', fontSize: '12px' }}>Refreshing...</span>}
      </div>

      {cameras.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '24px', color: '#64748b', fontSize: '13px' }}>
          No cameras registered yet. Complete the form above to add a monitoring point.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {cameras.map((cam) => {
            const isSelected = cam.id === selectedCameraId;
            const isOnline = cam.status === 'ONLINE';

            return (
              <div
                key={cam.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 16px',
                  backgroundColor: isSelected ? 'rgba(2, 132, 199, 0.15)' : '#0f172a',
                  border: isSelected ? '1px solid #0284c7' : '1px solid #334155',
                  borderRadius: '6px',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span
                      style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        backgroundColor: isOnline ? '#22c55e' : '#64748b',
                      }}
                    />
                    <strong style={{ color: '#f8fafc', fontSize: '14px' }}>{cam.name}</strong>
                    {isSelected && (
                      <span
                        style={{
                          backgroundColor: '#0284c7',
                          color: '#ffffff',
                          fontSize: '10px',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          fontWeight: 700,
                        }}
                      >
                        ACTIVE TARGET
                      </span>
                    )}
                  </div>

                  <span style={{ color: '#94a3b8', fontSize: '12px' }}>
                    📍 {cam.location}
                    {cam.latitude !== null && cam.longitude !== null && (
                      <span style={{ color: '#64748b', marginLeft: '6px' }}>
                        ({cam.latitude}, {cam.longitude})
                      </span>
                    )}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <button
                    onClick={() => onSelectCamera(cam)}
                    disabled={isSelected}
                    style={{
                      backgroundColor: isSelected ? '#0369a1' : '#334155',
                      color: '#ffffff',
                      border: 'none',
                      padding: '6px 12px',
                      borderRadius: '4px',
                      fontSize: '12px',
                      fontWeight: 600,
                      cursor: isSelected ? 'default' : 'pointer',
                    }}
                  >
                    {isSelected ? 'Selected' : 'Select'}
                  </button>

                  <button
                    onClick={() => onDeleteCamera(cam.id)}
                    title="Deactivate camera"
                    style={{
                      backgroundColor: 'transparent',
                      color: '#ef4444',
                      border: '1px solid #ef4444',
                      padding: '5px 10px',
                      borderRadius: '4px',
                      fontSize: '12px',
                      cursor: 'pointer',
                    }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

