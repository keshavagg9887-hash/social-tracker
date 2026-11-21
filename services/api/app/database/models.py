"""SQLAlchemy ORM Data Models [M3].

Schema definitions for PostgreSQL/PostGIS and SQLite supporting:
- Authentication, Users & Role-Based Access Control
- Camera Devices & Edge Streams
- Incidents, Detection Candidates, Deduplication & Correlation
- Immutable Audit Logs & Incident Timeline
- Responder Assignments & Response Lifecycle
- System Notifications & Alerts
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
from uuid import uuid4

def utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)

try:
    from sqlalchemy import (
        Boolean,
        Column,
        DateTime,
        Float,
        ForeignKey,
        Integer,
        String,
        Text,
    )
    from sqlalchemy.orm import declarative_base, relationship

    Base = declarative_base()
    HAVE_SQLALCHEMY = True
except ImportError:
    Base = object
    HAVE_SQLALCHEMY = False


if HAVE_SQLALCHEMY:

    class User(Base):
        """User account model with role-based access control."""
        __tablename__ = "users"

        id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
        email = Column(String(255), unique=True, nullable=False, index=True)
        hashed_password = Column(String(255), nullable=False)
        full_name = Column(String(255), nullable=False)
        role = Column(String(50), nullable=False, default="handler", index=True)  # admin, handler, viewer, authority
        is_active = Column(Boolean, default=True, nullable=False)
        created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
        updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

        def to_dict(self) -> Dict[str, Any]:
            return {
                "id": self.id,
                "email": self.email,
                "fullName": self.full_name,
                "role": self.role,
                "isActive": self.is_active,
                "createdAt": self.created_at.isoformat() if self.created_at else None,
                "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            }


    class Camera(Base):
        """Registered camera / edge device [M1 integration]."""
        __tablename__ = "cameras"

        id = Column(String(64), primary_key=True)
        name = Column(String(255), nullable=False)
        rtsp_url = Column(String(512), nullable=False)
        location = Column(String(255), nullable=False)
        latitude = Column(Float, nullable=True)
        longitude = Column(Float, nullable=True)
        is_active = Column(Boolean, default=True, nullable=False)
        status = Column(String(50), default="online", nullable=False)
        last_seen = Column(DateTime(timezone=True), default=utc_now, nullable=True)
        created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
        updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

        incidents = relationship("Incident", back_populates="camera", cascade="all, delete-orphan")

        def to_dict(self) -> Dict[str, Any]:
            return {
                "id": self.id,
                "name": self.name,
                "rtspUrl": self.rtsp_url,
                "location": self.location,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "isActive": self.is_active,
                "status": self.status,
                "lastSeen": self.last_seen.isoformat() if self.last_seen else None,
                "createdAt": self.created_at.isoformat() if self.created_at else None,
            }


    class Incident(Base):
        """Incident entity managed by the Incident Engine [M3]."""
        __tablename__ = "incidents"

        id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
        camera_id = Column(String(64), ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True, index=True)
        type = Column(String(50), nullable=False, index=True)
        severity = Column(String(50), nullable=False, default="medium", index=True)
        status = Column(String(50), nullable=False, default="detected", index=True)
        confidence = Column(Float, nullable=False)
        title = Column(String(255), nullable=False)
        description = Column(Text, nullable=True)
        location_reference = Column(String(255), nullable=True)
        latitude = Column(Float, nullable=True)
        longitude = Column(Float, nullable=True)
        evidence_reference = Column(String(512), nullable=False)
        bounding_boxes_json = Column(Text, default="[]", nullable=False)
        metadata_json = Column(Text, default="{}", nullable=False)
        
        detection_count = Column(Integer, default=1, nullable=False)
        deduplication_key = Column(String(128), nullable=True, index=True)
        merged_into_id = Column(String(36), nullable=True, index=True)

        reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
        reviewer_name = Column(String(255), nullable=True)
        review_notes = Column(Text, nullable=True)
        reviewed_at = Column(DateTime(timezone=True), nullable=True)

        created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
        updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

        camera = relationship("Camera", back_populates="incidents")
        timeline = relationship("IncidentAuditLog", back_populates="incident", cascade="all, delete-orphan", order_by="IncidentAuditLog.created_at.asc()")
        assignments = relationship("Assignment", back_populates="incident", cascade="all, delete-orphan", order_by="Assignment.created_at.desc()")

        @property
        def bounding_boxes(self) -> List[Dict[str, Any]]:
            try:
                return json.loads(self.bounding_boxes_json) if self.bounding_boxes_json else []
            except Exception:
                return []

        @bounding_boxes.setter
        def bounding_boxes(self, val: List[Dict[str, Any]]) -> None:
            self.bounding_boxes_json = json.dumps(val)

        @property
        def metadata_dict(self) -> Dict[str, Any]:
            try:
                return json.loads(self.metadata_json) if self.metadata_json else {}
            except Exception:
                return {}

        @metadata_dict.setter
        def metadata_dict(self, val: Dict[str, Any]) -> None:
            self.metadata_json = json.dumps(val)

        def to_dict(self) -> Dict[str, Any]:
            return {
                "id": self.id,
                "deviceId": self.camera_id,
                "cameraId": self.camera_id,
                "type": self.type,
                "severity": self.severity,
                "status": self.status,
                "confidence": self.confidence,
                "title": self.title,
                "description": self.description,
                "locationReference": self.location_reference,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "snapshotUrl": self.evidence_reference,
                "evidenceReference": self.evidence_reference,
                "boundingBoxes": self.bounding_boxes,
                "metadata": self.metadata_dict,
                "detectionCount": self.detection_count,
                "deduplicationKey": self.deduplication_key,
                "mergedIntoId": self.merged_into_id,
                "reviewerId": self.reviewer_id,
                "reviewerName": self.reviewer_name,
                "reviewNotes": self.review_notes,
                "reviewedAt": self.reviewed_at.isoformat() if self.reviewed_at else None,
                "timestamp": self.created_at.isoformat() if self.created_at else None,
                "createdAt": self.created_at.isoformat() if self.created_at else None,
                "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            }


    class IncidentAuditLog(Base):
        """Immutable audit trail and timeline of all incident actions [M3]."""
        __tablename__ = "incident_audit_logs"

        id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
        incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
        user_id = Column(String(36), nullable=True)
        user_name = Column(String(255), nullable=True)
        action = Column(String(50), nullable=False)
        previous_status = Column(String(50), nullable=True)
        new_status = Column(String(50), nullable=True)
        notes = Column(Text, nullable=True)
        metadata_json = Column(Text, default="{}", nullable=False)
        created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

        incident = relationship("Incident", back_populates="timeline")

        @property
        def metadata_dict(self) -> Dict[str, Any]:
            try:
                return json.loads(self.metadata_json) if self.metadata_json else {}
            except Exception:
                return {}

        @metadata_dict.setter
        def metadata_dict(self, val: Dict[str, Any]) -> None:
            self.metadata_json = json.dumps(val)

        def to_dict(self) -> Dict[str, Any]:
            return {
                "id": self.id,
                "incidentId": self.incident_id,
                "userId": self.user_id,
                "userName": self.user_name,
                "action": self.action,
                "previousStatus": self.previous_status,
                "newStatus": self.new_status,
                "notes": self.notes,
                "metadata": self.metadata_dict,
                "createdAt": self.created_at.isoformat() if self.created_at else None,
            }


    class Assignment(Base):
        """Response assignment and jurisdiction tracking [M3]."""
        __tablename__ = "assignments"

        id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
        incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
        assigned_by_id = Column(String(36), nullable=True)
        assigned_by_name = Column(String(255), nullable=True)
        responder_team = Column(String(255), nullable=False)
        authority_name = Column(String(255), nullable=False)
        status = Column(String(50), default="assigned", nullable=False, index=True)
        
        acknowledged_at = Column(DateTime(timezone=True), nullable=True)
        acknowledged_by = Column(String(255), nullable=True)
        response_notes = Column(Text, nullable=True)
        outcome = Column(Text, nullable=True)
        resolved_at = Column(DateTime(timezone=True), nullable=True)

        created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
        updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

        incident = relationship("Incident", back_populates="assignments")

        def to_dict(self) -> Dict[str, Any]:
            return {
                "id": self.id,
                "incidentId": self.incident_id,
                "assignedById": self.assigned_by_id,
                "assignedByName": self.assigned_by_name,
                "responderTeam": self.responder_team,
                "authorityName": self.authority_name,
                "status": self.status,
                "acknowledgedAt": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
                "acknowledgedBy": self.acknowledged_by,
                "responseNotes": self.response_notes,
                "outcome": self.outcome,
                "resolvedAt": self.resolved_at.isoformat() if self.resolved_at else None,
                "createdAt": self.created_at.isoformat() if self.created_at else None,
                "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            }


    class Notification(Base):
        """System and incident notification model [M3]."""
        __tablename__ = "notifications"

        id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
        user_id = Column(String(36), nullable=True, index=True)
        incident_id = Column(String(36), nullable=True, index=True)
        title = Column(String(255), nullable=False)
        message = Column(Text, nullable=False)
        severity = Column(String(50), default="medium", nullable=False)
        channel = Column(String(50), default="websocket", nullable=False)
        is_read = Column(Boolean, default=False, nullable=False)
        created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

        def to_dict(self) -> Dict[str, Any]:
            return {
                "id": self.id,
                "userId": self.user_id,
                "incidentId": self.incident_id,
                "title": self.title,
                "message": self.message,
                "severity": self.severity,
                "channel": self.channel,
                "isRead": self.is_read,
                "createdAt": self.created_at.isoformat() if self.created_at else None,
            }

else:
    # Standalone mock model definitions for environments without SQLAlchemy installed
    class User:
        def __init__(self, **kwargs):
            self.id = kwargs.get("id", str(uuid4()))
            self.email = kwargs.get("email", "")
            self.hashed_password = kwargs.get("hashed_password", "")
            self.full_name = kwargs.get("full_name", "")
            self.role = kwargs.get("role", "handler")
            self.is_active = kwargs.get("is_active", True)
            self.created_at = kwargs.get("created_at", utc_now())
            self.updated_at = kwargs.get("updated_at", utc_now())

        def to_dict(self):
            return {
                "id": self.id,
                "email": self.email,
                "fullName": self.full_name,
                "role": self.role,
                "isActive": self.is_active,
                "createdAt": self.created_at.isoformat() if self.created_at else None,
                "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            }

    class Camera:
        def __init__(self, **kwargs):
            self.id = kwargs.get("id", str(uuid4()))
            self.name = kwargs.get("name", "")
            self.rtsp_url = kwargs.get("rtsp_url", "")
            self.location = kwargs.get("location", "")
            self.latitude = kwargs.get("latitude")
            self.longitude = kwargs.get("longitude")
            self.is_active = kwargs.get("is_active", True)
            self.status = kwargs.get("status", "online")
            self.last_seen = kwargs.get("last_seen", utc_now())
            self.created_at = kwargs.get("created_at", utc_now())

        def to_dict(self):
            return {
                "id": self.id,
                "name": self.name,
                "rtspUrl": self.rtsp_url,
                "location": self.location,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "isActive": self.is_active,
                "status": self.status,
                "lastSeen": self.last_seen.isoformat() if self.last_seen else None,
                "createdAt": self.created_at.isoformat() if self.created_at else None,
            }

    class Incident:
        def __init__(self, **kwargs):
            self.id = kwargs.get("id", str(uuid4()))
            self.camera_id = kwargs.get("camera_id")
            self.type = kwargs.get("type", "unknown")
            self.severity = kwargs.get("severity", "medium")
            self.status = kwargs.get("status", "detected")
            self.confidence = kwargs.get("confidence", 0.0)
            self.title = kwargs.get("title", "")
            self.description = kwargs.get("description")
            self.location_reference = kwargs.get("location_reference")
            self.latitude = kwargs.get("latitude")
            self.longitude = kwargs.get("longitude")
            self.evidence_reference = kwargs.get("evidence_reference", "")
            self.bounding_boxes = kwargs.get("bounding_boxes", [])
            self.metadata_dict = kwargs.get("metadata_dict", {})
            self.detection_count = kwargs.get("detection_count", 1)
            self.deduplication_key = kwargs.get("deduplication_key")
            self.merged_into_id = kwargs.get("merged_into_id")
            self.reviewer_id = kwargs.get("reviewer_id")
            self.reviewer_name = kwargs.get("reviewer_name")
            self.review_notes = kwargs.get("review_notes")
            self.reviewed_at = kwargs.get("reviewed_at")
            self.created_at = kwargs.get("created_at", utc_now())
            self.updated_at = kwargs.get("updated_at", utc_now())

        def to_dict(self):
            return {
                "id": self.id,
                "deviceId": self.camera_id,
                "cameraId": self.camera_id,
                "type": self.type,
                "severity": self.severity,
                "status": self.status,
                "confidence": self.confidence,
                "title": self.title,
                "description": self.description,
                "locationReference": self.location_reference,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "snapshotUrl": self.evidence_reference,
                "evidenceReference": self.evidence_reference,
                "boundingBoxes": self.bounding_boxes,
                "metadata": self.metadata_dict,
                "detectionCount": self.detection_count,
                "deduplicationKey": self.deduplication_key,
                "mergedIntoId": self.merged_into_id,
                "reviewerId": self.reviewer_id,
                "reviewerName": self.reviewer_name,
                "reviewNotes": self.review_notes,
                "reviewedAt": self.reviewed_at.isoformat() if self.reviewed_at else None,
                "timestamp": self.created_at.isoformat() if self.created_at else None,
                "createdAt": self.created_at.isoformat() if self.created_at else None,
                "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            }

    class IncidentAuditLog:
        def __init__(self, **kwargs):
            self.id = kwargs.get("id", str(uuid4()))
            self.incident_id = kwargs.get("incident_id", "")
            self.user_id = kwargs.get("user_id")
            self.user_name = kwargs.get("user_name")
            self.action = kwargs.get("action", "")
            self.previous_status = kwargs.get("previous_status")
            self.new_status = kwargs.get("new_status")
            self.notes = kwargs.get("notes")
            self.metadata_dict = kwargs.get("metadata_dict", {})
            self.created_at = kwargs.get("created_at", utc_now())

        def to_dict(self):
            return {
                "id": self.id,
                "incidentId": self.incident_id,
                "userId": self.user_id,
                "userName": self.user_name,
                "action": self.action,
                "previousStatus": self.previous_status,
                "newStatus": self.new_status,
                "notes": self.notes,
                "metadata": self.metadata_dict,
                "createdAt": self.created_at.isoformat() if self.created_at else None,
            }

    class Assignment:
        def __init__(self, **kwargs):
            self.id = kwargs.get("id", str(uuid4()))
            self.incident_id = kwargs.get("incident_id", "")
            self.assigned_by_id = kwargs.get("assigned_by_id")
            self.assigned_by_name = kwargs.get("assigned_by_name")
            self.responder_team = kwargs.get("responder_team", "")
            self.authority_name = kwargs.get("authority_name", "")
            self.status = kwargs.get("status", "assigned")
            self.acknowledged_at = kwargs.get("acknowledged_at")
            self.acknowledged_by = kwargs.get("acknowledged_by")
            self.response_notes = kwargs.get("response_notes")
            self.outcome = kwargs.get("outcome")
            self.resolved_at = kwargs.get("resolved_at")
            self.created_at = kwargs.get("created_at", utc_now())
            self.updated_at = kwargs.get("updated_at", utc_now())

        def to_dict(self):
            return {
                "id": self.id,
                "incidentId": self.incident_id,
                "assignedById": self.assigned_by_id,
                "assignedByName": self.assigned_by_name,
                "responderTeam": self.responder_team,
                "authorityName": self.authority_name,
                "status": self.status,
                "acknowledgedAt": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
                "acknowledgedBy": self.acknowledged_by,
                "responseNotes": self.response_notes,
                "outcome": self.outcome,
                "resolvedAt": self.resolved_at.isoformat() if self.resolved_at else None,
                "createdAt": self.created_at.isoformat() if self.created_at else None,
                "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            }

    class Notification:
        def __init__(self, **kwargs):
            self.id = kwargs.get("id", str(uuid4()))
            self.user_id = kwargs.get("user_id")
            self.incident_id = kwargs.get("incident_id")
            self.title = kwargs.get("title", "")
            self.message = kwargs.get("message", "")
            self.severity = kwargs.get("severity", "medium")
            self.channel = kwargs.get("channel", "websocket")
            self.is_read = kwargs.get("is_read", False)
            self.created_at = kwargs.get("created_at", utc_now())

        def to_dict(self):
            return {
                "id": self.id,
                "userId": self.user_id,
                "incidentId": self.incident_id,
                "title": self.title,
                "message": self.message,
                "severity": self.severity,
                "channel": self.channel,
                "isRead": self.is_read,
                "createdAt": self.created_at.isoformat() if self.created_at else None,
            }
