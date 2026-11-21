"""Analytics Module Exports [M3]."""

try:
    from .router import router
except ImportError:
    router = None

from .schemas import AnalyticsSummaryResponse, CameraAnalyticsResponse, CameraStatItem

__all__ = [
    "router",
    "AnalyticsSummaryResponse",
    "CameraAnalyticsResponse",
    "CameraStatItem",
]
