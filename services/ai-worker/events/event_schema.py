"""AI Event Candidate Schema and Data Contracts [M2].

Agreed data contract between Person 2 (AI & Detection) and Person 3 (Backend & Incident Engine).
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class DetectionType(str, Enum):
    FIRE = "fire"
    SMOKE = "smoke"
    ACCIDENT = "accident"


class BoundingBox(BaseModel):
    """Normalized or absolute bounding box coordinates with detection label."""
    x1: float = Field(..., description="Top-left X coordinate")
    y1: float = Field(..., description="Top-left Y coordinate")
    x2: float = Field(..., description="Bottom-right X coordinate")
    y2: float = Field(..., description="Bottom-right Y coordinate")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    label: str = Field(..., description="Detected object label")
    tracker_id: Optional[int] = Field(None, description="Optional object tracker ID")


class AIDetectionCandidate(BaseModel):
    """AI-generated event candidate published to Redis Streams and Backend API.
    
    Key principle: An AI detection is an event candidate, not a confirmed emergency.
    Human review is required before consequential action.
    """
    event_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique candidate ID")
    detection_type: DetectionType = Field(..., description="Category of detection: fire, smoke, or accident")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Highest confidence score in candidate")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of occurrence"
    )
    camera_id: str = Field(..., description="Identifier of the source camera device")
    location_reference: Optional[str] = Field(None, description="Descriptive location or geo coordinates")
    evidence_reference: str = Field(..., description="URI or path to the stored snapshot/video evidence")
    bounding_boxes: List[BoundingBox] = Field(default_factory=list, description="Detected bounding boxes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context (e.g. vehicle count, FPS)")

    def to_redis_dict(self) -> Dict[str, str]:
        """Convert candidate to flat dictionary suitable for Redis Streams XADD."""
        import json
        return {
            "event_id": self.event_id,
            "detection_type": self.detection_type.value,
            "confidence": str(self.confidence),
            "timestamp": self.timestamp,
            "camera_id": self.camera_id,
            "location_reference": self.location_reference or "",
            "evidence_reference": self.evidence_reference,
            "bounding_boxes": json.dumps([b.model_dump() for b in self.bounding_boxes]),
            "metadata": json.dumps(self.metadata),
        }

    @classmethod
    def from_redis_dict(cls, data: Dict[bytes, bytes]) -> "AIDetectionCandidate":
        """Deserialize from Redis Stream message bytes."""
        import json

        def _decode(val: Any) -> str:
            if isinstance(val, bytes):
                return val.decode("utf-8")
            return str(val)

        d = {_decode(k): _decode(v) for k, v in data.items()}
        boxes_raw = json.loads(d.get("bounding_boxes", "[]"))
        meta_raw = json.loads(d.get("metadata", "{}"))

        return cls(
            event_id=d["event_id"],
            detection_type=DetectionType(d["detection_type"]),
            confidence=float(d["confidence"]),
            timestamp=d["timestamp"],
            camera_id=d["camera_id"],
            location_reference=d.get("location_reference") or None,
            evidence_reference=d["evidence_reference"],
            bounding_boxes=[BoundingBox(**b) for b in boxes_raw],
            metadata=meta_raw,
        )
