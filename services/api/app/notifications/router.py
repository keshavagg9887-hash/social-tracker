"""Notifications Router [M3].

Endpoints for retrieving and acknowledging system notifications.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.security import get_current_user
from ..database.models import Notification, User
from ..database.session import get_db
from .schemas import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=List[NotificationResponse],
    summary="List Notifications",
    description="Returns notifications for the authenticated user or system alerts.",
)
async def list_notifications(
    unread_only: bool = Query(False, description="Filter for unread alerts only"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[NotificationResponse]:
    stmt = select(Notification).order_by(Notification.created_at.desc()).limit(limit)
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    
    result = await db.execute(stmt)
    notifications = result.scalars().all()
    return [NotificationResponse(**n.to_dict()) for n in notifications]


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark Notification as Read",
)
async def mark_as_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationResponse:
    stmt = select(Notification).where(Notification.id == notification_id)
    result = await db.execute(stmt)
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return NotificationResponse(**notification.to_dict())


@router.post(
    "/read-all",
    summary="Mark All Notifications as Read",
)
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = update(Notification).values(is_read=True)
    await db.execute(stmt)
    await db.commit()
    return {"status": "ok", "message": "All notifications marked as read"}
