/**
 * Camera Location & Registration Form Component [M1].
 * Captures camera name, location text, and GPS coordinates with HTML5 Geolocation detection.
 */
import React, { useState } from 'react';
import { RegisterCameraPayload } from '../types/camera.types';
import { cameraService } from '../services/cameraService';

interface CameraLocationFormProps {
  onRegister: (payload: RegisterCameraPayload) => Promise<void>;
  isSubmitting?: boolean;
}

export const CameraLocationForm: React.FC<CameraLocationFormProps> = ({
  onRegister,
  isSubmitting = false,
}) => {
  const [name, setName] = useState('');
  const [location, setLocation] = useState('');
  const [latitude, setLatitude] = useState<string>('');
  const [longitude, setLongitude] = useState<string>('');
  const [isLocating, setIsLocating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const handleDetectLocation = async () => {
    setIsLocating(true);
    setFormError(null);
    try {
      const coords = await cameraService.getCurrentLocation();
      setLatitude(coords.latitude.toString());
      setLongitude(coords.longitude.toString());
    } catch (err: any) {
      setFormError(err.message || 'Failed to detect location');
    } finally {
      setIsLocating(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    const trimmedName = name.trim();
    const trimmedLoc = location.trim();

    if (!trimmedName) {
      setFormError('Please enter a valid camera name.');
      return;
    }
    if (!trimmedLoc) {
      setFormError('Please describe the camera location.');
      return;
    }

    let latNum: number | null = null;
    let lngNum: number | null = null;

    if (latitude.trim()) {
      latNum = parseFloat(latitude);
      if (isNaN(latNum) || latNum < -90 || latNum > 90) {
        setFormError('Latitude must be a valid number between -90 and 90.');
        return;
      }
    }

    if (longitude.trim()) {
      lngNum = parseFloat(longitude);
      if (isNaN(lngNum) || lngNum < -180 || lngNum > 180) {
        setFormError('Longitude must be a valid number between -180 and 180.');
        return;
      }
    }

    try {
      await onRegister({
        name: trimmedName,
        location: trimmedLoc,
        latitude: latNum,
        longitude: lngNum,
        device_metadata: {
          userAgent: navigator.userAgent,
          platform: navigator.platform,
          registeredVia: 'CameraClient',
        },
      });

      // Reset form
      setName('');
      setLocation('');
      setLatitude('');
      setLongitude('');
    } catch (err: any) {
      setFormError(err.message || 'Failed to register camera device');
    }
  };

  return (
    <div
      style={{
        backgroundColor: '#1e293b',
        padding: '20px',
        borderRadius: '8px',
        border: '1px solid #334155',
      }}
    >
      <h3 style={{ margin: '0 0 16px 0', color: '#f1f5f9', fontSize: '16px' }}>
        Register New Camera Device
      </h3>

      {formError && (
        <div
          style={{
            padding: '10px 14px',
            backgroundColor: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid #ef4444',
            borderRadius: '6px',
            color: '#fca5a5',
            fontSize: '13px',
            marginBottom: '16px',
          }}
        >
          {formError}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div>
          <label style={{ display: 'block', color: '#cbd5e1', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
            Camera Name *
          </label>
          <input
            type="text"
            placeholder="e.g. North Gate Webcam #1"
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={isSubmitting}
            required
            style={{
              width: '100%',
              boxSizing: 'border-box',
              padding: '8px 12px',
              backgroundColor: '#0f172a',
              border: '1px solid #475569',
              borderRadius: '6px',
              color: '#f8fafc',
              fontSize: '13px',
            }}
          />
        </div>

        <div>
          <label style={{ display: 'block', color: '#cbd5e1', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
            Location Description *
          </label>
          <input
            type="text"
            placeholder="e.g. Building C - 2nd Floor Corridor"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            disabled={isSubmitting}
            required
            style={{
              width: '100%',
              boxSizing: 'border-box',
              padding: '8px 12px',
              backgroundColor: '#0f172a',
              border: '1px solid #475569',
              borderRadius: '6px',
              color: '#f8fafc',
              fontSize: '13px',
            }}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <div>
            <label style={{ display: 'block', color: '#cbd5e1', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
              Latitude (-90 to 90)
            </label>
            <input
              type="number"
              step="any"
              placeholder="e.g. 37.7749"
              value={latitude}
              onChange={(e) => setLatitude(e.target.value)}
              disabled={isSubmitting}
              style={{
                width: '100%',
                boxSizing: 'border-box',
                padding: '8px 12px',
                backgroundColor: '#0f172a',
                border: '1px solid #475569',
                borderRadius: '6px',
                color: '#f8fafc',
                fontSize: '13px',
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', color: '#cbd5e1', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
              Longitude (-180 to 180)
            </label>
            <input
              type="number"
              step="any"
              placeholder="e.g. -122.4194"
              value={longitude}
              onChange={(e) => setLongitude(e.target.value)}
              disabled={isSubmitting}
              style={{
                width: '100%',
                boxSizing: 'border-box',
                padding: '8px 12px',
                backgroundColor: '#0f172a',
                border: '1px solid #475569',
                borderRadius: '6px',
                color: '#f8fafc',
                fontSize: '13px',
              }}
            />
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', marginTop: '6px' }}>
          <button
            type="button"
            onClick={handleDetectLocation}
            disabled={isSubmitting || isLocating}
            style={{
              flex: 1,
              backgroundColor: '#334155',
              color: '#f1f5f9',
              border: 'none',
              padding: '10px 14px',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: 600,
              cursor: isSubmitting || isLocating ? 'not-allowed' : 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
            }}
          >
            <span>📍</span> {isLocating ? 'Detecting GPS...' : 'Detect Coordinates'}
          </button>

          <button
            type="submit"
            disabled={isSubmitting}
            style={{
              flex: 1,
              backgroundColor: '#0284c7',
              color: '#ffffff',
              border: 'none',
              padding: '10px 14px',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: 700,
              cursor: isSubmitting ? 'not-allowed' : 'pointer',
            }}
          >
            {isSubmitting ? 'Registering...' : 'Register Camera'}
          </button>
        </div>
      </form>
    </div>
  );
};

