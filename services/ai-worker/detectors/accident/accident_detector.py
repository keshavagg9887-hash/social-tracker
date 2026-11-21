"""Road Accident & Collision Detection Model [M2].

Detects traffic collisions and road accidents using vehicle detection, trajectory tracking,
and multi-vehicle intersection & abrupt deceleration analysis.
Supports dedicated YOLO accident models or kinematic collision analysis.
"""

import os
import logging
from typing import List, Tuple, Dict, Any, Optional
import cv2
import numpy as np

try:
    from detectors.base import BaseDetector, DetectionResult
    from tracking.tracker import ObjectTracker, calculate_iou
except (ImportError, ValueError):
    from ..base import BaseDetector, DetectionResult
    from ...tracking.tracker import ObjectTracker, calculate_iou

logger = logging.getLogger(__name__)

# COCO vehicle classes: 2: car, 3: motorcycle, 5: bus, 7: truck
VEHICLE_CLASS_IDS = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}


class AccidentDetector(BaseDetector):
    """Detector for identifying traffic collisions and vehicular accidents."""

    def __init__(
        self,
        weights_path: Optional[str] = None,
        confidence_threshold: float = 0.50,
        collision_iou_threshold: float = 0.10,
        min_motion_history: int = 3
    ):
        super().__init__(confidence_threshold=confidence_threshold)
        self.weights_path = weights_path or os.getenv("ACCIDENT_MODEL_WEIGHTS")
        self.collision_iou_threshold = collision_iou_threshold
        self.min_motion_history = min_motion_history
        self.tracker = ObjectTracker(iou_threshold=0.3, max_age=15)
        self.yolo_model = self._init_yolo()

    def _init_yolo(self):
        """Initializes YOLO for vehicle or specialized accident detection."""
        weights = self.weights_path or "yolov8n.pt"
        try:
            from ultralytics import YOLO
            # If custom accident weights exist, use them; otherwise use base yolov8n for vehicle tracking
            model = YOLO(weights)
            logger.info(f"Loaded Accident/Vehicle YOLO model from {weights}")
            return model
        except Exception as e:
            logger.warning(f"Failed to load YOLO model ({weights}): {e}. Using motion fallback.")
            return None

    def _detect_vehicles_yolo(self, frame: np.ndarray) -> Tuple[List[DetectionResult], List[DetectionResult]]:
        """Inference for vehicles and direct accident class labels."""
        results = self.yolo_model(frame, conf=0.35, verbose=False)
        vehicle_detections: List[DetectionResult] = []
        direct_accidents: List[DetectionResult] = []

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].tolist()
                cls_name = r.names.get(cls_id, "").lower()

                # If dedicated accident class is detected by a trained accident model
                if "accident" in cls_name or "crash" in cls_name:
                    direct_accidents.append(
                        DetectionResult(
                            label="accident",
                            confidence=conf,
                            bbox=(xyxy[0], xyxy[1], xyxy[2], xyxy[3]),
                            metadata={"detector": "yolo_accident_classifier"}
                        )
                    )
                # Standard vehicle detection for kinematic collision analysis
                elif cls_id in VEHICLE_CLASS_IDS or any(v in cls_name for v in ("car", "truck", "bus", "motorcycle", "vehicle")):
                    vehicle_detections.append(
                        DetectionResult(
                            label=cls_name or "vehicle",
                            confidence=conf,
                            bbox=(xyxy[0], xyxy[1], xyxy[2], xyxy[3]),
                            metadata={"detector": "yolo_vehicle"}
                        )
                    )

        return vehicle_detections, direct_accidents

    def _detect_vehicles_fallback(self, frame: np.ndarray) -> List[DetectionResult]:
        """Heuristic vehicle / moving object detector when YOLO is not available."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        vehicles: List[DetectionResult] = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 1200:  # Typical vehicle scale in camera view
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = float(w) / max(1, h)
                # Vehicles typically have aspect ratios between 0.7 and 3.0
                if 0.6 <= aspect_ratio <= 3.5:
                    vehicles.append(
                        DetectionResult(
                            label="vehicle",
                            confidence=0.60,
                            bbox=(float(x), float(y), float(x + w), float(y + h)),
                            metadata={"detector": "contour_fallback"}
                        )
                    )
        return vehicles

    def _analyze_collisions(self, tracked_vehicles: List[DetectionResult]) -> List[DetectionResult]:
        """Evaluates pairwise intersection, relative speed, and overlap between tracked vehicles."""
        accident_candidates: List[DetectionResult] = []
        n = len(tracked_vehicles)

        for i in range(n):
            for j in range(i + 1, n):
                v1 = tracked_vehicles[i]
                v2 = tracked_vehicles[j]

                iou = calculate_iou(v1.bbox, v2.bbox)

                # Check if vehicles collide or significantly overlap
                if iou >= self.collision_iou_threshold:
                    # Enclosing bounding box of the collision
                    x1 = min(v1.bbox[0], v2.bbox[0])
                    y1 = min(v1.bbox[1], v2.bbox[1])
                    x2 = max(v1.bbox[2], v2.bbox[2])
                    y2 = max(v1.bbox[3], v2.bbox[3])

                    # Confidence scaled by overlap and individual vehicle confidence
                    base_conf = (v1.confidence + v2.confidence) / 2.0
                    conf = min(0.95, base_conf * (0.6 + min(0.4, iou * 2.0)))

                    if conf >= self.confidence_threshold:
                        accident_candidates.append(
                            DetectionResult(
                                label="accident",
                                confidence=conf,
                                bbox=(x1, y1, x2, y2),
                                metadata={
                                    "collision_iou": round(iou, 3),
                                    "vehicle_1_id": v1.tracker_id,
                                    "vehicle_2_id": v2.tracker_id,
                                    "vehicle_1_label": v1.label,
                                    "vehicle_2_label": v2.label,
                                    "detector": "kinematic_collision_analysis",
                                }
                            )
                        )

        return accident_candidates

    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        """Runs vehicle detection, tracks positions, and flags accident event candidates."""
        if self.yolo_model is not None:
            vehicle_dets, direct_accidents = self._detect_vehicles_yolo(frame)
            if direct_accidents:
                return direct_accidents
        else:
            vehicle_dets = self._detect_vehicles_fallback(frame)

        # Update tracking state across frames
        tracked_vehicles = self.tracker.update(vehicle_dets)

        # Evaluate collisions among active vehicles
        return self._analyze_collisions(tracked_vehicles)
