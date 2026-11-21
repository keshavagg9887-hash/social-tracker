"""Incident Lifecycle & Management Router [M3].

Provides endpoints for:
- Listing and filtering incidents (status, severity, camera, type)
- Human Review: Confirm, Reject, Mark Inconclusive, Merge Duplicates
- Real-time Timeline and Audit Trail retrieval
"""

from datetime import datetime, timezone
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.security import get_current_user, require_roles
from ..database.models import Incident, IncidentAuditLog, User
from ..database.session import get_db
from ..websocket.manager import ws_manager
from .schemas import (
    IncidentAuditLogResponse,
    IncidentListResponse,
    IncidentMergeRequest,
    IncidentResponse,
    IncidentReviewRequest,
    IncidentStatusUpdate,
)

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get(
    "",
    response_model=IncidentListResponse,
    summary="List Incidents with Filters",
    description="Retrieve paginated list of incidents filtered by status, type, severity, camera, or search query.",
)
async def list_incidents(
    status: Optional[str] = Query(None, description="detected, reviewing, confirmed, rejected, inconclusive, merged, dispatched, resolved"),
    type: Optional[str] = Query(None, description="fire, smoke, accident"),
    severity: Optional[str] = Query(None, description="low, medium, high, critical"),
    camera_id: Optional[str] = Query(None, description="Filter by camera device ID"),
    search: Optional[str] = Query(None, description="Search by title or location"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IncidentListResponse:
    stmt = select(Incident).order_by(Incident.created_at.desc())

    if status:
        stmt = stmt.where(Incident.status == status)
    if type:
        stmt = stmt.where(Incident.type == type)
    if severity:
        stmt = stmt.where(Incident.severity == severity)
    if camera_id:
        stmt = stmt.where(Incident.camera_id == camera_id)
    if search:
        search_filter = f"%{search.strip()}%"
        stmt = stmt.where(
            Incident.title.ilike(search_filter) | Incident.location_reference.ilike(search_filter)
        )

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Paginate
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    result = await db.execute(stmt)
    incidents = result.scalars().all()

    return IncidentListResponse(
        items=[IncidentResponse(**i.to_dict()) for i in incidents],
        total=total,
        page=page,
        pageSize=page_size,
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Get Incident Details",
)
async def get_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IncidentResponse:
    stmt = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(stmt)
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    return IncidentResponse(**incident.to_dict())


@router.post(
    "/{incident_id}/confirm",
    response_model=IncidentResponse,
    summary="Confirm Incident (Handler Verification)",
    description="Handler confirms an AI detection candidate as a legitimate incident.",
)
async def confirm_incident(
    incident_id: str,
    payload: IncidentReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "handler")),
) -> IncidentResponse:
    stmt = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(stmt)
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    prev_status = incident.status
    incident.status = "confirmed"
    incident.reviewer_id = current_user.id
    incident.reviewer_name = current_user.full_name
    incident.review_notes = payload.notes
    incident.reviewed_at = datetime.now(timezone.utc)

    # Add audit log
    audit_log = IncidentAuditLog(
        incident_id=incident.id,
        user_id=current_user.id,
        user_name=current_user.full_name,
        action="confirmed",
        previous_status=prev_status,
        new_status="confirmed",
        notes=payload.notes or "Incident verified and confirmed by handler.",
    )
    db.add(audit_log)
    await db.commit()
    await db.refresh(incident)

    # Broadcast update
    await ws_manager.broadcast({
        "type": "incident_confirmed",
        "incident": incident.to_dict(),
        "handler": current_user.full_name,
    })
    return IncidentResponse(**incident.to_dict())


@router.post(
    "/{incident_id}/reject",
    response_model=IncidentResponse,
    summary="Reject Incident (False Positive)",
    description="Handler rejects candidate as a false alarm or non-emergency.",
)
async def reject_incident(
    incident_id: str,
    payload: IncidentReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "handler")),
) -> IncidentResponse:
    stmt = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(stmt)
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    prev_status = incident.status
    incident.status = "rejected"
    incident.reviewer_id = current_user.id
    incident.reviewer_name = current_user.full_name
    incident.review_notes = payload.notes or "Marked as false positive."
    incident.reviewed_at = datetime.now(timezone.utc)

    # Add audit log
    audit_log = IncidentAuditLog(
        incident_id=incident.id,
        user_id=current_user.id,
        user_name=current_user.full_name,
        action="rejected",
        previous_status=prev_status,
        new_status="rejected",
        notes=payload.notes or "Candidate rejected as false alarm.",
    )
    db.add(audit_log)
    await db.commit()
    await db.refresh(incident)

    # Broadcast update
    await ws_manager.broadcast({
        "type": "incident_rejected",
        "incident": incident.to_dict(),
        "handler": current_user.full_name,
    })
    return IncidentResponse(**incident.to_dict())


@router.post(
    "/{incident_id}/inconclusive",
    response_model=IncidentResponse,
    summary="Mark Incident as Inconclusive",
    description="Flag candidate as needing further observation or additional video footage.",
)
async def mark_inconclusive(
    incident_id: str,
    payload: IncidentReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "handler")),
) -> IncidentResponse:
    stmt = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(stmt)
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    prev_status = incident.status
    incident.status = "inconclusive"
    incident.reviewer_id = current_user.id
    incident.reviewer_name = current_user.full_name
    incident.review_notes = payload.notes
    incident.reviewed_at = datetime.now(timezone.utc)

    audit_log = IncidentAuditLog(
        incident_id=incident.id,
        user_id=current_user.id,
        user_name=current_user.full_name,
        action="inconclusive",
        previous_status=prev_status,
        new_status="inconclusive",
        notes=payload.notes or "Marked as inconclusive; awaiting further evidence.",
    )
    db.add(audit_log)
    await db.commit()
    await db.refresh(incident)

    await ws_manager.broadcast({
        "type": "incident_inconclusive",
        "incident": incident.to_dict(),
    })
    return IncidentResponse(**incident.to_dict())


@router.post(
    "/{incident_id}/merge",
    response_model=IncidentResponse,
    summary="Merge Duplicate Incident",
    description="Merges a duplicate incident into a target primary incident.",
)
async def merge_incident(
    incident_id: str,
    payload: IncidentMergeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "handler")),
) -> IncidentResponse:
    if incident_id == payload.targetIncidentId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot merge an incident into itself")

    stmt_source = select(Incident).where(Incident.id == incident_id)
    result_source = await db.execute(stmt_source)
    source_incident = result_source.scalar_one_or_none()

    stmt_target = select(Incident).where(Incident.id == payload.targetIncidentId)
    result_target = await db.execute(stmt_target)
    target_incident = result_target.scalar_one_or_none()

    if not source_incident or not target_incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source or target incident not found")

    prev_status = source_incident.status
    source_incident.status = "merged"
    source_incident.merged_into_id = target_incident.id

    # Update target incident detection count
    target_incident.detection_count += source_incident.detection_count

    # Audit logs on both
    source_audit = IncidentAuditLog(
        incident_id=source_incident.id,
        user_id=current_user.id,
        user_name=current_user.full_name,
        action="merged",
        previous_status=prev_status,
        new_status="merged",
        notes=f"Merged into target incident {target_incident.id}. Reason: {payload.notes or 'Duplicate event'}",
    )
    target_audit = IncidentAuditLog(
        incident_id=target_incident.id,
        user_id=current_user.id,
        user_name=current_user.full_name,
        action="correlated_event",
        previous_status=target_incident.status,
        new_status=target_incident.status,
        notes=f"Absorbed duplicate incident {source_incident.id}. Total detections: {target_incident.detection_count}.",
    )
    db.add(source_audit)
    db.add(target_audit)
    await db.commit()
    await db.refresh(source_incident)

    await ws_manager.broadcast({
        "type": "incident_merged",
        "sourceIncidentId": source_incident.id,
        "targetIncidentId": target_incident.id,
    })
    return IncidentResponse(**source_incident.to_dict())


@router.patch(
    "/{incident_id}/status",
    response_model=IncidentResponse,
    summary="Update Incident Status",
)
async def update_status(
    incident_id: str,
    payload: IncidentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "handler", "authority")),
) -> IncidentResponse:
    stmt = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(stmt)
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    prev_status = incident.status
    incident.status = payload.status

    audit_log = IncidentAuditLog(
        incident_id=incident.id,
        user_id=current_user.id,
        user_name=current_user.full_name,
        action="status_change",
        previous_status=prev_status,
        new_status=payload.status,
        notes=payload.notes or f"Status transitioned from {prev_status} to {payload.status}",
    )
    db.add(audit_log)
    await db.commit()
    await db.refresh(incident)

    await ws_manager.broadcast({
        "type": "incident_status_updated",
        "incident": incident.to_dict(),
    })
    return IncidentResponse(**incident.to_dict())


@router.get(
    "/{incident_id}/timeline",
    response_model=List[IncidentAuditLogResponse],
    summary="Get Incident Audit Timeline",
    description="Returns chronological audit trail for verification, assignment, notes, and resolution.",
)
async def get_incident_timeline(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[IncidentAuditLogResponse]:
    stmt = (
        select(IncidentAuditLog)
        .where(IncidentAuditLog.incident_id == incident_id)
        .order_by(IncidentAuditLog.created_at.asc())
    )
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return [IncidentAuditLogResponse(**log.to_dict()) for log in logs]
