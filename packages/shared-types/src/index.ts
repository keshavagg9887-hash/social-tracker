// Shared Domain Models & Types [M4]

export type Role = 'admin' | 'handler' | 'viewer';

export interface User {
  id: string;
  email: string;
  fullName: string;
  role: Role;
  createdAt: string;
}

export type IncidentSeverity = 'low' | 'medium' | 'high' | 'critical';
export type IncidentType = 'fire' | 'smoke' | 'accident' | 'security';
export type IncidentStatus = 'detected' | 'reviewing' | 'dispatched' | 'resolved';

export interface Incident {
  id: string;
  deviceId: string;
  type: IncidentType;
  severity: IncidentSeverity;
  status: IncidentStatus;
  confidence: number;
  timestamp: string;
  snapshotUrl?: string;
}

export interface CameraDevice {
  id: string;
  name: string;
  rtspUrl: string;
  location: string;
  isActive: boolean;
}
