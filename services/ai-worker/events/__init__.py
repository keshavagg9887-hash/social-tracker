"""Events module for AI Detection Worker [M2]."""

from .event_schema import AIDetectionCandidate, BoundingBox, DetectionType

__all__ = [
    "AIDetectionCandidate",
    "BoundingBox",
    "DetectionType",
    "EvidenceManager",
    "EventPublisher",
]

def __getattr__(name: str):
    if name == "EvidenceManager":
        from .evidence_manager import EvidenceManager
        return EvidenceManager
    elif name == "EventPublisher":
        from .publisher import EventPublisher
        return EventPublisher
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
