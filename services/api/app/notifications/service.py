"""Notification Dispatch Service [M3].

Persists notifications in database, broadcasts to live WebSockets,
and pushes alert messages to Redis for the notification-worker.
"""

import json
import logging
from typing import Optional
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database.models import Notification
from ..websocket.manager import ws_manager

logger = logging.getLogger(__name__)


async def create_and_dispatch_notification(
    db: AsyncSession,
    title: str,
    message: str,
    severity: str = "medium",
    channel: str = "websocket",
    user_id: Optional[str] = None,
    incident_id: Optional[str] = None,
) -> Notification:
    """Creates a notification record and dispatches it across channels."""
    notification = Notification(
        user_id=user_id,
        incident_id=incident_id,
        title=title,
        message=message,
        severity=severity,
        channel=channel,
        is_read=False,
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)

    # 1. Real-time WebSocket broadcast
    try:
        await ws_manager.broadcast({
            "type": "notification_received",
            "notification": notification.to_dict(),
        })
    except Exception as e:
        logger.warning(f"Failed to broadcast notification via WebSocket: {e}")

    # 2. Redis stream dispatch for Notification Worker
    try:
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await r.xadd(
            settings.REDIS_STREAM_NOTIFICATIONS,
            {
                "notification_id": notification.id,
                "incident_id": incident_id or "",
                "title": title,
                "message": message,
                "severity": severity,
                "channel": channel,
                "created_at": notification.created_at.isoformat(),
            },
        )
        await r.aclose()
    except Exception as e:
        logger.debug(f"Redis notification dispatch skipped or failed (worker will read from DB/poll): {e}")

    return notification
