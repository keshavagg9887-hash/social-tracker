"""Tests for Fire, Smoke, and Accident Detectors [M2]."""

import unittest
import numpy as np

try:
    import cv2
    from detectors.fire.fire_detector import FireDetector
    from detectors.smoke.smoke_detector import SmokeDetector
    from detectors.accident.accident_detector import AccidentDetector
    from detectors.base import DetectionResult
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


class TestDetectors(unittest.TestCase):

    def setUp(self):
        if not HAS_CV2:
            self.skipTest("cv2 (OpenCV) is not installed in the host environment.")

    def test_fire_detector_on_clean_frame(self):
        detector = FireDetector(confidence_threshold=0.5)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        results = detector.detect(frame)
        self.assertEqual(len(results), 0)

    def test_fire_detector_on_synthetic_flame(self):
        detector = FireDetector(confidence_threshold=0.4, temporal_window=1, min_contour_area=50)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.rectangle(frame, (100, 100), (200, 200), (0, 120, 255), -1)

        results = detector.detect(frame)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].label, "fire")
        self.assertGreaterEqual(results[0].confidence, 0.4)

    def test_smoke_detector_on_clean_frame(self):
        detector = SmokeDetector(confidence_threshold=0.45)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        results = detector.detect(frame)
        self.assertEqual(len(results), 0)

    def test_accident_collision_detection(self):
        detector = AccidentDetector(confidence_threshold=0.5, collision_iou_threshold=0.10)
        v1 = DetectionResult(label="car", confidence=0.85, bbox=(100.0, 100.0, 200.0, 200.0), tracker_id=1)
        v2 = DetectionResult(label="truck", confidence=0.80, bbox=(150.0, 150.0, 250.0, 250.0), tracker_id=2)

        candidates = detector._analyze_collisions([v1, v2])
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].label, "accident")
        self.assertEqual(candidates[0].metadata["vehicle_1_id"], 1)
        self.assertEqual(candidates[0].metadata["vehicle_2_id"], 2)


if __name__ == "__main__":
    unittest.main()
