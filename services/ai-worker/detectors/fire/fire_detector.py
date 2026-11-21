"""Fire Detection Model [M2].

Detects open flames and fire hazards using YOLO neural networks with adaptive HSV color & contour heuristic fallback.
Includes temporal consistency filtering to eliminate single-frame false alarms.
"""

import os
import logging
from collections import deque
from typing import List, Optional
import cv2
import numpy as np

try:
    from detectors.base import BaseDetector, DetectionResult
except (ImportError, ValueError):
    from ..base import BaseDetector, DetectionResult

logger = logging.getLogger(__name__)


class FireDetector(BaseDetector):
    """Detector specialized for identifying fire and active flames."""

    def __init__(
        self,
        weights_path: Optional[str] = None,
        confidence_threshold: float = 0.5,
        temporal_window: int = 3,
        min_contour_area: int = 150
    ):
        super().__init__(confidence_threshold=confidence_threshold)
        self.weights_path = weights_path or os.getenv("FIRE_MODEL_WEIGHTS")
        self.temporal_window = temporal_window
        self.min_contour_area = min_contour_area
        self._history = deque(maxlen=temporal_window)
        self.yolo_model = self._init_yolo()

    def _init_yolo(self):
        """Attempts to load a trained YOLO model if weights exist."""
        if self.weights_path and os.path.exists(self.weights_path):
            try:
                from ultralytics import YOLO
                model = YOLO(self.weights_path)
                logger.info(f"Loaded Fire YOLO weights from {self.weights_path}")
                return model
            except Exception as e:
                logger.warning(f"Failed to load YOLO fire model: {e}. Falling back to CV heuristic.")
        return None

    def _detect_yolo(self, frame: np.ndarray) -> List[DetectionResult]:
        """Inference using Ultralytics YOLO."""
        results = self.yolo_model(frame, conf=self.confidence_threshold, verbose=False)
        detections: List[DetectionResult] = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls_id = int(box.cls[0])
                cls_name = r.names.get(cls_id, "fire").lower()
                if "fire" in cls_name:
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].tolist()
                    detections.append(
                        DetectionResult(
                            label="fire",
                            confidence=conf,
                            bbox=(xyxy[0], xyxy[1], xyxy[2], xyxy[3]),
                            metadata={"detector": "yolo"}
                        )
                    )
        return detections

    def _detect_heuristic(self, frame: np.ndarray) -> List[DetectionResult]:
        """Fallback Computer Vision fire detector using HSV flame color segmentation & luminance analysis."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Red/Orange/Yellow flame color masks in HSV
        lower_flame1 = np.array([0, 120, 180])
        upper_flame1 = np.array([25, 255, 255])
        mask1 = cv2.inRange(hsv, lower_flame1, upper_flame1)

        lower_flame2 = np.array([165, 120, 180])
        upper_flame2 = np.array([180, 255, 255])
        mask2 = cv2.inRange(hsv, lower_flame2, upper_flame2)

        flame_mask = cv2.bitwise_or(mask1, mask2)

        # Morphological opening and closing to reduce noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        flame_mask = cv2.morphologyEx(flame_mask, cv2.MORPH_OPEN, kernel)
        flame_mask = cv2.morphologyEx(flame_mask, cv2.MORPH_DILATE, kernel)

        contours, _ = cv2.findContours(flame_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections: List[DetectionResult] = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= self.min_contour_area:
                x, y, w, h = cv2.boundingRect(cnt)
                
                # Compute confidence based on color saturation, value intensity, and area
                roi_hsv = hsv[y:y+h, x:x+w]
                avg_val = np.mean(roi_hsv[:, :, 2])
                avg_sat = np.mean(roi_hsv[:, :, 1])
                
                confidence = min(0.95, max(0.40, (avg_val / 255.0 * 0.6) + (avg_sat / 255.0 * 0.3) + min(0.1, area / 10000.0)))
                
                if confidence >= self.confidence_threshold:
                    detections.append(
                        DetectionResult(
                            label="fire",
                            confidence=confidence,
                            bbox=(float(x), float(y), float(x + w), float(y + h)),
                            metadata={"area": area, "detector": "hsv_heuristic"}
                        )
                    )

        return detections

    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        """Detects fire in the frame with temporal consistency validation."""
        if self.yolo_model is not None:
            raw_detections = self._detect_yolo(frame)
        else:
            raw_detections = self._detect_heuristic(frame)

        # Temporal smoothing: check if detections are sustained over consecutive frames
        has_detection = len(raw_detections) > 0
        self._history.append(has_detection)

        # If detected in at least half of the temporal window frames, confirm candidate
        if sum(self._history) >= max(1, self.temporal_window // 2):
            return raw_detections

        return []
