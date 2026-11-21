"""AI Detections FastAPI Package [M2]."""

from .schemas import AIDetectionEventCandidate, AIDetectionResponse, DetectionType, BoundingBox

try:
    from .router import router
except ImportError:
    router = None

__all__ = [
    "router",
    "AIDetectionEventCandidate",
    "AIDetectionResponse",
    "DetectionType",
    "BoundingBox",
]
