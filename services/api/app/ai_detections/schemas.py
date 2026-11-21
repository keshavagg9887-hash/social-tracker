"""AI Detection Schemas & Data Contracts for FastAPI Backend [M2].

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
    """Bounding box coordinates with confidence score and label."""
    x1: float = Field(..., description="Top-left X coordinate")
    y1: float = Field(..., description="Top-left Y coordinate")
    x2: float = Field(..., description="Bottom-right X coordinate")
    y2: float = Field(..., description="Bottom-right Y coordinate")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    label: str = Field(..., description="Detected object label")
    tracker_id: Optional[int] = Field(None, description="Optional object tracker ID")


class AIDetectionEventCandidate(BaseModel):
    """Payload sent by AI Worker when an incident event candidate is detected.
    
    Key principle: An AI detection is an event candidate, not a confirmed emergency.
    Human review is required before consequential action.
    """
    event_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique candidate ID")
    detection_type: DetectionType = Field(..., description="Category: fire, smoke, or accident")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC ISO-8601 timestamp"
    )
    camera_id: str = Field(..., description="Camera identifier")
    location_reference: Optional[str] = Field(None, description="Location description or coordinates")
    evidence_reference: str = Field(..., description="URI or path to the snapshot evidence image")
    bounding_boxes: List[BoundingBox] = Field(default_factory=list, description="Bounding boxes of detections")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context metadata")


class AIDetectionResponse(BaseModel):
    """Acknowledgement response returned to the AI worker."""
    status: str = Field(..., example="received")
    event_id: str
    message: str = Field(..., example="Event candidate queued for incident processing")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
