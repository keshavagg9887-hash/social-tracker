"""Analytics Router [M3].

Provides aggregate reporting, incident metrics, false positive rates,
and per-camera hotspot statistics.
"""

from typing import Dict
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.security import get_current_user
from ..database.models import Assignment, Incident, User
from ..database.session import get_db
from .schemas import AnalyticsSummaryResponse, CameraAnalyticsResponse, CameraStatItem

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/summary",
    response_model=AnalyticsSummaryResponse,
    summary="Get Incident Analytics Summary",
    description="Returns aggregate statistics on incidents, severities, types, and resolution times.",
)
async def get_analytics_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyticsSummaryResponse:
    # 1. Total incidents
    total_res = await db.execute(select(func.count(Incident.id)))
    total = total_res.scalar_one() or 0

    # 2. Count by type
    type_res = await db.execute(select(Incident.type, func.count(Incident.id)).group_by(Incident.type))
    by_type = {t or "unknown": c for t, c in type_res.all()}

    # 3. Count by severity
    sev_res = await db.execute(select(Incident.severity, func.count(Incident.id)).group_by(Incident.severity))
    by_sev = {s or "unknown": c for s, c in sev_res.all()}

    # 4. Count by status
    status_res = await db.execute(select(Incident.status, func.count(Incident.id)).group_by(Incident.status))
    by_status = {st or "unknown": c for st, c in status_res.all()}

    active_statuses = {"detected", "reviewing", "confirmed", "dispatched"}
    active_count = sum(by_status.get(s, 0) for s in active_statuses)
    resolved_count = by_status.get("resolved", 0)
    false_alarms = by_status.get("rejected", 0)

    # 5. Average resolution time calculation from resolved assignments
    avg_minutes = None
    resolved_assignments_res = await db.execute(
        select(Assignment).where(Assignment.resolved_at.is_not(None))
    )
    resolved_assignments = resolved_assignments_res.scalars().all()
    durations = [
        (a.resolved_at - a.created_at).total_seconds() / 60.0
        for a in resolved_assignments
        if a.resolved_at and a.created_at
    ]
    if durations:
        avg_minutes = round(sum(durations) / len(durations), 1)

    return AnalyticsSummaryResponse(
        totalIncidents=total,
        activeIncidents=active_count,
        resolvedIncidents=resolved_count,
        falseAlarms=false_alarms,
        byType=by_type,
        bySeverity=by_sev,
        byStatus=by_status,
        averageResolutionMinutes=avg_minutes,
    )


@router.get(
    "/camera-stats",
    response_model=CameraAnalyticsResponse,
    summary="Get Hotspot Stats per Camera Device",
)
async def get_camera_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CameraAnalyticsResponse:
    stmt = (
        select(
            Incident.camera_id,
            func.count(Incident.id).label("total"),
            func.max(Incident.created_at).label("last_at"),
        )
        .where(Incident.camera_id.is_not(None))
        .group_by(Incident.camera_id)
    )
    result = await db.execute(stmt)
    rows = result.all()

    camera_items = []
    for cam_id, count, last_at in rows:
        # Check active
        active_stmt = select(func.count(Incident.id)).where(
            Incident.camera_id == cam_id,
            Incident.status.in_(["detected", "reviewing", "confirmed", "dispatched"]),
        )
        active_res = await db.execute(active_stmt)
        active_count = active_res.scalar_one() or 0

        camera_items.append(
            CameraStatItem(
                cameraId=cam_id,
                incidentCount=count,
                activeCount=active_count,
                lastIncidentAt=last_at.isoformat() if last_at else None,
            )
        )

    return CameraAnalyticsResponse(cameras=camera_items)
