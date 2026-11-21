"""Assignments & Response Coordination Router [M3].

Endpoints for:
- Dispatching / assigning incidents to emergency authorities
- Responder acknowledgement & ETA logging
- On-scene progress and status updates
- Resolution and incident closure
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.security import get_current_user, require_roles
from ..database.models import Assignment, Incident, IncidentAuditLog, User
from ..database.session import get_db
from ..notifications.service import create_and_dispatch_notification
from ..websocket.manager import ws_manager
from .schemas import (
    AssignmentAcknowledge,
    AssignmentCreate,
    AssignmentProgress,
    AssignmentResolve,
    AssignmentResponse,
)

router = APIRouter(tags=["Assignments"])


@router.post(
    "/incidents/{incident_id}/assignments",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign Incident to Authority / Responder Team",
    description="Assigns a confirmed incident to a designated authority and transitions status to 'dispatched'.",
)
async def assign_incident(
    incident_id: str,
    payload: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "handler")),
) -> AssignmentResponse:
    stmt = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(stmt)
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    # Transition incident status to dispatched
    prev_status = incident.status
    incident.status = "dispatched"

    # Create assignment
    assignment = Assignment(
        incident_id=incident.id,
        assigned_by_id=current_user.id,
        assigned_by_name=current_user.full_name,
        responder_team=payload.responderTeam,
        authority_name=payload.authorityName,
        status="assigned",
        response_notes=payload.notes,
    )
    db.add(assignment)

    # Timeline audit
    audit = IncidentAuditLog(
        incident_id=incident.id,
        user_id=current_user.id,
        user_name=current_user.full_name,
        action="assigned",
        previous_status=prev_status,
        new_status="dispatched",
        notes=f"Assigned to {payload.authorityName} ({payload.responderTeam}). Notes: {payload.notes or 'None'}",
    )
    db.add(audit)
    await db.commit()
    await db.refresh(assignment)
    await db.refresh(incident)

    # Broadcast update
    await ws_manager.broadcast({
        "type": "incident_assigned",
        "incident": incident.to_dict(),
        "assignment": assignment.to_dict(),
    })

    # Dispatch notification
    await create_and_dispatch_notification(
        db=db,
        title=f"Incident Dispatched: {incident.title}",
        message=f"Incident {incident.id} assigned to {assignment.authority_name} ({assignment.responder_team}).",
        severity=incident.severity,
        channel="websocket",
        incident_id=incident.id,
    )

    return AssignmentResponse(**assignment.to_dict())


@router.get(
    "/assignments",
    response_model=List[AssignmentResponse],
    summary="List Response Assignments",
)
async def list_assignments(
    incident_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[AssignmentResponse]:
    stmt = select(Assignment).order_by(Assignment.created_at.desc())
    if incident_id:
        stmt = stmt.where(Assignment.incident_id == incident_id)
    if status:
        stmt = stmt.where(Assignment.status == status)

    result = await db.execute(stmt)
    assignments = result.scalars().all()
    return [AssignmentResponse(**a.to_dict()) for a in assignments]


@router.get(
    "/assignments/{assignment_id}",
    response_model=AssignmentResponse,
    summary="Get Assignment Details",
)
async def get_assignment(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssignmentResponse:
    stmt = select(Assignment).where(Assignment.id == assignment_id)
    result = await db.execute(stmt)
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    return AssignmentResponse(**assignment.to_dict())


@router.post(
    "/assignments/{assignment_id}/acknowledge",
    response_model=AssignmentResponse,
    summary="Acknowledge Assignment",
    description="Authority or responder records receipt and acceptance of the assignment.",
)
async def acknowledge_assignment(
    assignment_id: str,
    payload: AssignmentAcknowledge,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "handler", "authority")),
) -> AssignmentResponse:
    stmt = select(Assignment).where(Assignment.id == assignment_id)
    result = await db.execute(stmt)
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    assignment.status = "acknowledged"
    assignment.acknowledged_at = datetime.now(timezone.utc)
    assignment.acknowledged_by = payload.acknowledgedBy
    if payload.notes:
        assignment.response_notes = (
            f"{assignment.response_notes}\n[Ack]: {payload.notes}" if assignment.response_notes else payload.notes
        )

    # Timeline audit
    audit = IncidentAuditLog(
        incident_id=assignment.incident_id,
        user_id=current_user.id,
        user_name=current_user.full_name,
        action="acknowledged",
        notes=f"Response acknowledged by {payload.acknowledgedBy}. Remarks: {payload.notes or 'None'}",
    )
    db.add(audit)
    await db.commit()
    await db.refresh(assignment)

    await ws_manager.broadcast({
        "type": "assignment_acknowledged",
        "assignment": assignment.to_dict(),
    })
    return AssignmentResponse(**assignment.to_dict())


@router.post(
    "/assignments/{assignment_id}/progress",
    response_model=AssignmentResponse,
    summary="Record Response Progress / Updates",
    description="Logs real-time updates from responders in the field (e.g. en_route, on_scene).",
)
async def record_progress(
    assignment_id: str,
    payload: AssignmentProgress,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "handler", "authority")),
) -> AssignmentResponse:
    stmt = select(Assignment).where(Assignment.id == assignment_id)
    result = await db.execute(stmt)
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    assignment.status = payload.status
    formatted_note = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')} - {payload.status.upper()}]: {payload.notes}"
    assignment.response_notes = (
        f"{assignment.response_notes}\n{formatted_note}" if assignment.response_notes else formatted_note
    )

    audit = IncidentAuditLog(
        incident_id=assignment.incident_id,
        user_id=current_user.id,
        user_name=current_user.full_name,
        action="progress_update",
        notes=f"Status: {payload.status.upper()}. Notes: {payload.notes}",
    )
    db.add(audit)
    await db.commit()
    await db.refresh(assignment)

    await ws_manager.broadcast({
        "type": "assignment_progress_updated",
        "assignment": assignment.to_dict(),
    })
    return AssignmentResponse(**assignment.to_dict())


@router.post(
    "/assignments/{assignment_id}/resolve",
    response_model=AssignmentResponse,
    summary="Resolve Assignment and Close Incident",
    description="Records resolution outcome, closes the assignment, and updates the incident status to 'resolved'.",
)
async def resolve_assignment(
    assignment_id: str,
    payload: AssignmentResolve,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "handler")),
) -> AssignmentResponse:
    stmt = select(Assignment).where(Assignment.id == assignment_id)
    result = await db.execute(stmt)
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    now = datetime.now(timezone.utc)
    assignment.status = "resolved"
    assignment.outcome = payload.outcome
    assignment.resolved_at = now
    if payload.notes:
        assignment.response_notes = (
            f"{assignment.response_notes}\n[Resolution]: {payload.notes}" if assignment.response_notes else payload.notes
        )

    # Automatically resolve parent incident
    stmt_inc = select(Incident).where(Incident.id == assignment.incident_id)
    result_inc = await db.execute(stmt_inc)
    incident = result_inc.scalar_one_or_none()

    if incident:
        prev_status = incident.status
        incident.status = "resolved"

        audit = IncidentAuditLog(
            incident_id=incident.id,
            user_id=current_user.id,
            user_name=current_user.full_name,
            action="resolved",
            previous_status=prev_status,
            new_status="resolved",
            notes=f"Incident resolved by {assignment.authority_name}. Outcome: {payload.outcome}",
        )
        db.add(audit)

    await db.commit()
    await db.refresh(assignment)

    await ws_manager.broadcast({
        "type": "incident_resolved",
        "incidentId": assignment.incident_id,
        "assignment": assignment.to_dict(),
        "outcome": payload.outcome,
    })

    if incident:
        await create_and_dispatch_notification(
            db=db,
            title=f"Incident Resolved: {incident.title}",
            message=f"Incident {incident.id} marked as resolved. Outcome: {payload.outcome}",
            severity="low",
            channel="websocket",
            incident_id=incident.id,
        )

    return AssignmentResponse(**assignment.to_dict())
