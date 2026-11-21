/**
 * Camera Selector Component [M1].
 * Lists connected webcams and permits runtime switching between video inputs.
 */
import React from 'react';
import { CameraDeviceInfo } from '../types/camera.types';

interface CameraSelectorProps {
  devices: CameraDeviceInfo[];
  selectedDeviceId: string;
  onSelectDevice: (deviceId: string) => void;
  onRefresh: () => void;
  disabled?: boolean;
}

export const CameraSelector: React.FC<CameraSelectorProps> = ({
  devices,
  selectedDeviceId,
  onSelectDevice,
  onRefresh,
  disabled = false,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        backgroundColor: '#1e293b',
        padding: '12px 16px',
        borderRadius: '8px',
        border: '1px solid #334155',
      }}
    >
      <label
        style={{
          color: '#cbd5e1',
          fontSize: '13px',
          fontWeight: 600,
          whiteSpace: 'nowrap',
        }}
      >
        Select Webcam:
      </label>

      <select
        value={selectedDeviceId}
        onChange={(e) => onSelectDevice(e.target.value)}
        disabled={disabled || devices.length === 0}
        style={{
          flex: 1,
          backgroundColor: '#0f172a',
          color: '#f8fafc',
          border: '1px solid #475569',
          borderRadius: '6px',
          padding: '8px 12px',
          fontSize: '13px',
          outline: 'none',
          cursor: disabled ? 'not-allowed' : 'pointer',
        }}
      >
        {devices.length === 0 ? (
          <option value="">No webcam detected</option>
        ) : (
          devices.map((d, idx) => (
            <option key={d.deviceId || idx} value={d.deviceId}>
              {d.label || `Camera ${idx + 1}`}
            </option>
          ))
        )}
      </select>

      <button
        onClick={onRefresh}
        disabled={disabled}
        title="Refresh connected devices"
        style={{
          backgroundColor: '#334155',
          color: '#e2e8f0',
          border: 'none',
          padding: '8px 14px',
          borderRadius: '6px',
          cursor: disabled ? 'not-allowed' : 'pointer',
          fontSize: '13px',
          fontWeight: 600,
        }}
      >
        ↻ Refresh
      </button>
    </div>
  );
};

