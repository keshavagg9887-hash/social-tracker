"""Analytics Schemas [M3]."""

from typing import Dict, List, Optional
from pydantic import BaseModel


class AnalyticsSummaryResponse(BaseModel):
    totalIncidents: int
    activeIncidents: int
    resolvedIncidents: int
    falseAlarms: int
    byType: Dict[str, int]
    bySeverity: Dict[str, int]
    byStatus: Dict[str, int]
    averageResolutionMinutes: Optional[float] = None


class CameraStatItem(BaseModel):
    cameraId: str
    incidentCount: int
    activeCount: int
    lastIncidentAt: Optional[str] = None


class CameraAnalyticsResponse(BaseModel):
    cameras: List[CameraStatItem]
