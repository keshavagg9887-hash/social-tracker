"""Unit tests for AI Detections API Schema & Contracts [M2]."""

import unittest
from app.ai_detections.schemas import (
    AIDetectionEventCandidate,
    AIDetectionResponse,
    BoundingBox,
    DetectionType,
)


class TestAIDetectionsSchema(unittest.TestCase):

    def test_schema_valid_candidate(self):
        candidate = AIDetectionEventCandidate(
            detection_type=DetectionType.FIRE,
            confidence=0.91,
            camera_id="cam_main_st",
            location_reference="Downtown Sector 4",
            evidence_reference="/evidence/20261121/cam_main_st/snap_01.jpg",
            bounding_boxes=[
                BoundingBox(
                    x1=50.0,
                    y1=60.0,
                    x2=200.0,
                    y2=220.0,
                    confidence=0.91,
                    label="fire",
                    tracker_id=None,
                )
            ],
            metadata={"source": "unit_test", "fps": 3.0},
        )

        self.assertEqual(candidate.detection_type, DetectionType.FIRE)
        self.assertAlmostEqual(candidate.confidence, 0.91)
        self.assertEqual(len(candidate.bounding_boxes), 1)
        self.assertEqual(candidate.bounding_boxes[0].label, "fire")
        self.assertTrue(len(candidate.event_id) > 10)

    def test_schema_invalid_confidence(self):
        with self.assertRaises(ValueError):
            # Confidence must be between 0.0 and 1.0
            AIDetectionEventCandidate(
                detection_type=DetectionType.ACCIDENT,
                confidence=1.5,  # Invalid
                camera_id="cam_01",
                evidence_reference="/evidence/snap.jpg",
            )

    def test_response_model(self):
        resp = AIDetectionResponse(
            status="received",
            event_id="test-1234",
            message="Queued for review",
        )
        self.assertEqual(resp.status, "received")
        self.assertEqual(resp.event_id, "test-1234")


if __name__ == "__main__":
    unittest.main()
