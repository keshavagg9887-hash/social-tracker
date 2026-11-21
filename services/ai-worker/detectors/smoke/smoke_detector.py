"""Smoke Detection Model [M2].

Detects diffuse smoke plumes and hazy smoke formations using YOLO neural networks
with an adaptive HSV low-saturation & edge-diffusion heuristic fallback.
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


class SmokeDetector(BaseDetector):
    """Detector specialized for identifying smoke patterns and haze plumes."""

    def __init__(
        self,
        weights_path: Optional[str] = None,
        confidence_threshold: float = 0.45,
        temporal_window: int = 4,
        min_contour_area: int = 300
    ):
        super().__init__(confidence_threshold=confidence_threshold)
        self.weights_path = weights_path or os.getenv("SMOKE_MODEL_WEIGHTS")
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
                logger.info(f"Loaded Smoke YOLO weights from {self.weights_path}")
                return model
            except Exception as e:
                logger.warning(f"Failed to load YOLO smoke model: {e}. Falling back to CV heuristic.")
        return None

    def _detect_yolo(self, frame: np.ndarray) -> List[DetectionResult]:
        """Inference using Ultralytics YOLO."""
        results = self.yolo_model(frame, conf=self.confidence_threshold, verbose=False)
        detections: List[DetectionResult] = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                cls_name = r.names.get(cls_id, "smoke").lower()
                if "smoke" in cls_name:
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].tolist()
                    detections.append(
                        DetectionResult(
                            label="smoke",
                            confidence=conf,
                            bbox=(xyxy[0], xyxy[1], xyxy[2], xyxy[3]),
                            metadata={"detector": "yolo"}
                        )
                    )
        return detections

    def _detect_heuristic(self, frame: np.ndarray) -> List[DetectionResult]:
        """Fallback Computer Vision smoke detector identifying diffuse low-saturation regions with high transparency/blur."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Smoke is characterized by low color saturation and mid-to-high brightness
        lower_smoke = np.array([0, 0, 70])
        upper_smoke = np.array([180, 50, 230])
        smoke_mask = cv2.inRange(hsv, lower_smoke, upper_smoke)

        # Clean up isolated pixels
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        smoke_mask = cv2.morphologyEx(smoke_mask, cv2.MORPH_OPEN, kernel)
        smoke_mask = cv2.morphologyEx(smoke_mask, cv2.MORPH_DILATE, kernel)

        contours, _ = cv2.findContours(smoke_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections: List[DetectionResult] = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= self.min_contour_area:
                x, y, w, h = cv2.boundingRect(cnt)
                
                # Check texture sharpness in the bounding region: smoke reduces local edge sharpness
                roi_gray = gray[y:y+h, x:x+w]
                laplacian_var = cv2.Laplacian(roi_gray, cv2.CV_64F).var()

                # Low Laplacian variance indicates diffuse/blurry texture (typical of smoke plume)
                sharpness_penalty = min(0.3, laplacian_var / 500.0)
                base_confidence = 0.50 + min(0.35, (area / 15000.0)) - sharpness_penalty
                confidence = max(0.40, min(0.90, base_confidence))

                if confidence >= self.confidence_threshold:
                    detections.append(
                        DetectionResult(
                            label="smoke",
                            confidence=confidence,
                            bbox=(float(x), float(y), float(x + w), float(y + h)),
                            metadata={"area": area, "laplacian_var": round(laplacian_var, 2), "detector": "smoke_heuristic"}
                        )
                    )

        return detections

    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        """Detects smoke with temporal persistence filtering."""
        if self.yolo_model is not None:
            raw_detections = self._detect_yolo(frame)
        else:
            raw_detections = self._detect_heuristic(frame)

        has_detection = len(raw_detections) > 0
        self._history.append(has_detection)

        # Confirm when detected consistently across temporal window
        if sum(self._history) >= max(1, self.temporal_window // 2):
            return raw_detections

        return []
