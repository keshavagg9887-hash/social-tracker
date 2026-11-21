"""Incident Engine Core [M3].

Normalizes incoming AI event candidates, classifies incident severity,
performs spatial/temporal deduplication, correlates recurring detections,
and maintains audit trails.
"""

from datetime import datetime, timedelta, timezone
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from ..config import settings

logger = logging.getLogger(__name__)

# Graceful import for SQLAlchemy and database dependencies
try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from ..database.models import Incident, IncidentAuditLog, User
    from ..notifications.service import create_and_dispatch_notification
    from ..websocket.manager import ws_manager
except ImportError:
    select = None
    AsyncSession = None
    Incident = None
    IncidentAuditLog = None
    User = None
    create_and_dispatch_notification = None
    ws_manager = None


class IncidentEngine:
    """Core Engine responsible for turning AI detections into verified incidents."""

    @staticmethod
    def calculate_severity(detection_type: str, confidence: float, bounding_boxes: List[Dict[str, Any]]) -> str:
        """Classify severity into low, medium, high, or critical."""
        d_type = detection_type.lower()
        box_count = len(bounding_boxes)

        if d_type == "fire":
            if confidence >= 0.85 or box_count >= 2:
                return "critical"
            if confidence >= 0.70:
                return "high"
            return "medium"

        elif d_type == "accident":
            if confidence >= 0.85 or box_count >= 3:
                return "critical"
            if confidence >= 0.70:
                return "high"
            return "medium"

        elif d_type == "smoke":
            if confidence >= 0.85:
                return "high"
            if confidence >= 0.60:
                return "medium"
            return "low"

        return "medium"

    @classmethod
    async def process_candidate(
        cls,
        db: Any,
        candidate_data: Dict[str, Any],
    ) -> Tuple[Any, bool]:
        """Process an AI detection candidate:

        1. Normalize and extract candidate fields.
        2. Deduplicate and correlate with existing active incidents within window.
        3. If duplicate/recurring, update existing incident, bump detection count & add timeline log.
        4. If new, create incident in 'detected' status, log to timeline, push WS and alert.

        Returns (incident, is_new).
        """
        if not Incident or not select:
            raise RuntimeError("Database models are not available in this environment.")

        camera_id = str(candidate_data.get("camera_id") or "camera-unknown")
        detection_type = str(candidate_data.get("detection_type") or "unknown").lower()
        confidence = float(candidate_data.get("confidence") or 0.0)
        evidence_ref = str(candidate_data.get("evidence_reference") or "")
        location_ref = candidate_data.get("location_reference") or f"Location of {camera_id}"
        boxes = candidate_data.get("bounding_boxes") or []
        metadata = candidate_data.get("metadata") or {}

        dedup_key = f"{camera_id}:{detection_type}"
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            seconds=settings.INCIDENT_DEDUPLICATION_WINDOW_SECONDS
        )

        # Query for active matching incidents within the deduplication window
        stmt = (
            select(Incident)
            .where(
                Incident.deduplication_key == dedup_key,
                Incident.status.in_(["detected", "reviewing", "confirmed", "dispatched"]),
                Incident.created_at >= cutoff_time,
            )
            .order_by(Incident.created_at.desc())
        )
        result = await db.execute(stmt)
        existing_incident = result.scalar_one_or_none()

        if existing_incident:
            # Correlate into existing incident
            existing_incident.detection_count += 1
            if confidence > existing_incident.confidence:
                existing_incident.confidence = confidence
                existing_incident.evidence_reference = evidence_ref
                existing_incident.bounding_boxes = boxes

            # Append audit log
            audit_log = IncidentAuditLog(
                incident_id=existing_incident.id,
                action="correlated_event",
                previous_status=existing_incident.status,
                new_status=existing_incident.status,
                notes=(
                    f"Correlated recurring {detection_type} detection candidate. "
                    f"Confidence: {confidence:.2f}. Total occurrences: {existing_incident.detection_count}."
                ),
                metadata_json=json.dumps({
                    "event_id": candidate_data.get("event_id"),
                    "confidence": confidence,
                    "evidence_reference": evidence_ref,
                }),
            )
            db.add(audit_log)
            await db.commit()
            await db.refresh(existing_incident)

            # Broadcast update over WebSocket
            if ws_manager:
                await ws_manager.broadcast({
                    "type": "incident_correlated",
                    "incident": existing_incident.to_dict(),
                })
            logger.info(
                f"[Incident Engine] Correlated candidate into active incident {existing_incident.id} "
                f"(count: {existing_incident.detection_count})"
            )
            return existing_incident, False

        # Create brand-new incident candidate
        severity = cls.calculate_severity(detection_type, confidence, boxes)
        title = f"Potential {detection_type.capitalize()} on {camera_id}"

        new_incident = Incident(
            id=str(uuid4()),
            camera_id=camera_id,
            type=detection_type,
            severity=severity,
            status="detected",  # Candidate awaiting Handler review
            confidence=confidence,
            title=title,
            description=f"Automated AI detection candidate detected at {camera_id}. Human review required.",
            location_reference=location_ref,
            evidence_reference=evidence_ref,
            bounding_boxes=boxes,
            metadata_dict=metadata,
            detection_count=1,
            deduplication_key=dedup_key,
        )
        db.add(new_incident)
        await db.flush()

        # Initial audit log
        initial_log = IncidentAuditLog(
            incident_id=new_incident.id,
            action="created",
            new_status="detected",
            notes=f"AI Candidate event detected. Severity classified as {severity.upper()}. Awaiting Handler review.",
            metadata_json=json.dumps({
                "event_id": candidate_data.get("event_id"),
                "confidence": confidence,
                "evidence_reference": evidence_ref,
            }),
        )
        db.add(initial_log)
        await db.commit()
        await db.refresh(new_incident)

        # Broadcast new incident via WebSocket to handlers
        if ws_manager:
            await ws_manager.broadcast({
                "type": "incident_created",
                "incident": new_incident.to_dict(),
            })

        # Send alert notification
        if create_and_dispatch_notification:
            await create_and_dispatch_notification(
                db=db,
                title=f"New Candidate: {new_incident.title}",
                message=f"High-priority {new_incident.type} candidate ({new_incident.severity}) requires handler review.",
                severity=new_incident.severity,
                channel="websocket",
                incident_id=new_incident.id,
            )

        logger.info(f"[Incident Engine] Created new incident candidate {new_incident.id} ({title})")
        return new_incident, True
