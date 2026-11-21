"""Incident Lifecycle & Review Unit Tests [M3].

Tests human review actions (confirm, reject, inconclusive, merge)
and assignment coordination.
"""

import unittest
from app.database.models import Incident, IncidentAuditLog, Assignment


class TestIncidentLifecycle(unittest.TestCase):

    def test_incident_model_lifecycle_states(self):
        incident = Incident(
            id="inc-test-01",
            camera_id="cam_main_st",
            type="fire",
            severity="high",
            status="detected",
            confidence=0.82,
            title="Potential Fire on cam_main_st",
            evidence_reference="/evidence/snap_01.jpg",
            bounding_boxes=[{"x1": 10, "y1": 10, "x2": 50, "y2": 50, "label": "fire"}],
            metadata_dict={"fps": 5.0},
        )

        d = incident.to_dict()
        self.assertEqual(d["status"], "detected")
        self.assertEqual(d["type"], "fire")
        self.assertEqual(d["severity"], "high")
        self.assertEqual(len(d["boundingBoxes"]), 1)
        self.assertEqual(d["detectionCount"], 1)

        # Simulate handler confirmation
        incident.status = "confirmed"
        incident.reviewer_name = "Handler Alice"
        incident.review_notes = "Verified visible flames near building."

        d_conf = incident.to_dict()
        self.assertEqual(d_conf["status"], "confirmed")
        self.assertEqual(d_conf["reviewerName"], "Handler Alice")

    def test_assignment_lifecycle(self):
        assignment = Assignment(
            id="assign-01",
            incident_id="inc-test-01",
            assigned_by_name="Handler Alice",
            responder_team="Station 4 Engine",
            authority_name="City Fire Department",
            status="assigned",
        )

        d_assign = assignment.to_dict()
        self.assertEqual(d_assign["status"], "assigned")
        self.assertEqual(d_assign["authorityName"], "City Fire Department")

        # Simulate responder acknowledgement
        assignment.status = "acknowledged"
        assignment.acknowledged_by = "Captain Miller"
        self.assertEqual(assignment.to_dict()["status"], "acknowledged")
        self.assertEqual(assignment.to_dict()["acknowledgedBy"], "Captain Miller")

        # Simulate resolution
        assignment.status = "resolved"
        assignment.outcome = "Fire successfully contained."
        self.assertEqual(assignment.to_dict()["status"], "resolved")
        self.assertEqual(assignment.to_dict()["outcome"], "Fire successfully contained.")


if __name__ == "__main__":
    unittest.main()
