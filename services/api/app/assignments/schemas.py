"""Assignments & Response Tracking Schemas [M3]."""

from typing import Optional
from pydantic import BaseModel, Field


class AssignmentCreate(BaseModel):
    responderTeam: str = Field(..., description="e.g. Station 4 Fire Crew, Traffic Unit 12")
    authorityName: str = Field(..., description="e.g. Metropolitan Fire Dept, Highway Police, EMS")
    notes: Optional[str] = Field(None, description="Initial dispatch instructions")


class AssignmentAcknowledge(BaseModel):
    acknowledgedBy: str = Field(..., description="Responder / Dispatcher name")
    notes: Optional[str] = Field(None, description="Acknowledgement remarks or ETA")


class AssignmentProgress(BaseModel):
    status: str = Field(..., description="en_route, on_scene, active")
    notes: str = Field(..., description="Field update or progress notes")


class AssignmentResolve(BaseModel):
    outcome: str = Field(..., description="Summary of incident resolution and final actions taken")
    notes: Optional[str] = Field(None, description="Additional closing remarks")


class AssignmentResponse(BaseModel):
    id: str
    incidentId: str
    assignedById: Optional[str] = None
    assignedByName: Optional[str] = None
    responderTeam: str
    authorityName: str
    status: str
    acknowledgedAt: Optional[str] = None
    acknowledgedBy: Optional[str] = None
    responseNotes: Optional[str] = None
    outcome: Optional[str] = None
    resolvedAt: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
