"""Incident Schemas & DTOs [M3]."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IncidentResponse(BaseModel):
    id: str
    deviceId: Optional[str] = None
    cameraId: Optional[str] = None
    type: str
    severity: str
    status: str
    confidence: float
    title: str
    description: Optional[str] = None
    locationReference: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    snapshotUrl: str
    evidenceReference: str
    boundingBoxes: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    detectionCount: int = 1
    deduplicationKey: Optional[str] = None
    mergedIntoId: Optional[str] = None
    reviewerId: Optional[str] = None
    reviewerName: Optional[str] = None
    reviewNotes: Optional[str] = None
    reviewedAt: Optional[str] = None
    timestamp: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class IncidentListResponse(BaseModel):
    items: List[IncidentResponse]
    total: int
    page: int
    pageSize: int


class IncidentReviewRequest(BaseModel):
    notes: Optional[str] = Field(None, description="Review remarks or reasons for confirmation/rejection")


class IncidentMergeRequest(BaseModel):
    targetIncidentId: str = Field(..., description="ID of the canonical incident into which this is merged")
    notes: Optional[str] = Field(None, description="Merge remarks")


class IncidentStatusUpdate(BaseModel):
    status: str = Field(..., description="detected, reviewing, confirmed, rejected, inconclusive, merged, dispatched, resolved")
    notes: Optional[str] = None


class IncidentAuditLogResponse(BaseModel):
    id: str
    incidentId: str
    userId: Optional[str] = None
    userName: Optional[str] = None
    action: str
    previousStatus: Optional[str] = None
    newStatus: Optional[str] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = {}
    createdAt: Optional[str] = None
