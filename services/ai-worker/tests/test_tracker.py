"""Tests for Object Tracker and IoU calculations [M2]."""

import unittest
from tracking.tracker import ObjectTracker, calculate_iou
from detectors.base import DetectionResult


class TestObjectTracker(unittest.TestCase):

    def test_calculate_iou(self):
        # Identical boxes -> IoU = 1.0
        boxA = (0.0, 0.0, 10.0, 10.0)
        boxB = (0.0, 0.0, 10.0, 10.0)
        self.assertAlmostEqual(calculate_iou(boxA, boxB), 1.0)

        # Non-overlapping boxes -> IoU = 0.0
        boxC = (20.0, 20.0, 30.0, 30.0)
        self.assertAlmostEqual(calculate_iou(boxA, boxC), 0.0)

        # 50% overlap box (5x10 overlap, union is 150) -> IoU = 50 / 150 = 0.333
        boxD = (5.0, 0.0, 15.0, 10.0)
        self.assertAlmostEqual(calculate_iou(boxA, boxD), 50.0 / 150.0, places=3)

    def test_tracker_assignment(self):
        tracker = ObjectTracker(iou_threshold=0.3)

        # Frame 1: One vehicle detected
        det1 = [DetectionResult(label="car", confidence=0.9, bbox=(10.0, 10.0, 50.0, 50.0))]
        updated1 = tracker.update(det1)
        self.assertIsNotNone(updated1[0].tracker_id)
        assigned_id = updated1[0].tracker_id

        # Frame 2: Vehicle slightly moved
        det2 = [DetectionResult(label="car", confidence=0.88, bbox=(12.0, 12.0, 52.0, 52.0))]
        updated2 = tracker.update(det2)
        self.assertEqual(updated2[0].tracker_id, assigned_id)


if __name__ == "__main__":
    unittest.main()
