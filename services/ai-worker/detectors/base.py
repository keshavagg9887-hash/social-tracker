"""Base Detector Interface [M2].

Common abstraction and data structures for all vision detection models.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional
import numpy as np


@dataclass
class DetectionResult:
    """Individual object or phenomenon detection result."""
    label: str
    confidence: float
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2) in pixel or normalized coords
    tracker_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "confidence": round(self.confidence, 4),
            "bbox": [round(float(c), 2) for c in self.bbox],
            "tracker_id": self.tracker_id,
            "metadata": self.metadata,
        }


class BaseDetector(ABC):
    """Abstract base class for all computer vision detectors."""

    def __init__(self, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold

    @abstractmethod
    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        """Runs inference on a video frame and returns a list of detections exceeding the confidence threshold."""
        pass
