"""Tests for Event Schema, Serialization, and Evidence Snapshots [M2]."""

import os
import shutil
import unittest
import numpy as np
from events.event_schema import AIDetectionCandidate, BoundingBox, DetectionType

try:
    import cv2
    from events.evidence_manager import EvidenceManager
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


class TestEvents(unittest.TestCase):

    def setUp(self):
        self.test_evidence_dir = "test_evidence"
        if HAS_CV2:
            self.evidence_mgr = EvidenceManager(base_storage_dir=self.test_evidence_dir)

    def tearDown(self):
        if os.path.exists(self.test_evidence_dir):
            shutil.rmtree(self.test_evidence_dir)

    def test_candidate_serialization(self):
        candidate = AIDetectionCandidate(
            detection_type=DetectionType.FIRE,
            confidence=0.89,
            camera_id="cam_test_01",
            location_reference="North Gate",
            evidence_reference="/evidence/20261121/cam_test_01/test.jpg",
            bounding_boxes=[
                BoundingBox(x1=10, y1=20, x2=100, y2=150, confidence=0.89, label="fire")
            ],
            metadata={"source": "test"}
        )

        # To Redis dict
        redis_dict = candidate.to_redis_dict()
        self.assertIn("event_id", redis_dict)
        self.assertEqual(redis_dict["detection_type"], "fire")

        # From Redis dict
        byte_dict = {k.encode("utf-8"): v.encode("utf-8") for k, v in redis_dict.items()}
        restored = AIDetectionCandidate.from_redis_dict(byte_dict)

        self.assertEqual(restored.event_id, candidate.event_id)
        self.assertEqual(restored.detection_type, DetectionType.FIRE)
        self.assertAlmostEqual(restored.confidence, 0.89)
        self.assertEqual(len(restored.bounding_boxes), 1)
        self.assertEqual(restored.bounding_boxes[0].label, "fire")

    def test_evidence_snapshot_generation(self):
        if not HAS_CV2:
            self.skipTest("cv2 (OpenCV) is not installed in the host environment.")

        frame = np.full((480, 640, 3), 120, dtype=np.uint8)
        boxes = [BoundingBox(x1=50, y1=50, x2=150, y2=150, confidence=0.92, label="fire")]

        ref = self.evidence_mgr.save_snapshot(
            frame=frame,
            event_id="test_ev_01",
            camera_id="cam_99",
            detection_type="fire",
            bounding_boxes=boxes
        )

        self.assertTrue(ref.startswith("/evidence/"))
        self.assertIn("cam_99", ref)
        self.assertIn("test_ev_01.jpg", ref)


if __name__ == "__main__":
    unittest.main()
