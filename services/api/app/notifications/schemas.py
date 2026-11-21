"""Notifications Schemas [M3]."""

from typing import Optional
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: str
    userId: Optional[str] = None
    incidentId: Optional[str] = None
    title: str
    message: str
    severity: str
    channel: str
    isRead: bool
    createdAt: Optional[str] = None


class NotificationCreate(BaseModel):
    title: str
    message: str
    severity: str = "medium"
    channel: str = "websocket"
    user_id: Optional[str] = None
    incident_id: Optional[str] = None
