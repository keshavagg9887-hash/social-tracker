"""Incidents Module Exports [M3]."""

try:
    from .router import router
except ImportError:
    router = None

try:
    from .consumer import RedisIncidentConsumer, redis_consumer
except ImportError:
    RedisIncidentConsumer = None
    redis_consumer = None

from .engine import IncidentEngine
from .schemas import (
    IncidentAuditLogResponse,
    IncidentListResponse,
    IncidentMergeRequest,
    IncidentResponse,
    IncidentReviewRequest,
    IncidentStatusUpdate,
)

__all__ = [
    "router",
    "IncidentEngine",
    "RedisIncidentConsumer",
    "redis_consumer",
    "IncidentResponse",
    "IncidentListResponse",
    "IncidentReviewRequest",
    "IncidentMergeRequest",
    "IncidentStatusUpdate",
    "IncidentAuditLogResponse",
]
