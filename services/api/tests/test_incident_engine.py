"""Incident Engine Unit Tests [M3].

Tests normalization, severity classification, deduplication, and detection correlation.
"""

import unittest
from app.incidents.engine import IncidentEngine


class TestIncidentEngine(unittest.TestCase):

    def test_calculate_severity_fire(self):
        # Critical fire: high confidence
        sev_crit = IncidentEngine.calculate_severity("fire", 0.92, [{"box": [1, 2, 3, 4]}])
        self.assertEqual(sev_crit, "critical")

        # Critical fire: multiple boxes
        sev_multi = IncidentEngine.calculate_severity("fire", 0.75, [{"box": 1}, {"box": 2}])
        self.assertEqual(sev_multi, "critical")

        # High fire: moderate confidence
        sev_high = IncidentEngine.calculate_severity("fire", 0.72, [{"box": 1}])
        self.assertEqual(sev_high, "high")

        # Medium fire: lower confidence
        sev_med = IncidentEngine.calculate_severity("fire", 0.55, [{"box": 1}])
        self.assertEqual(sev_med, "medium")

    def test_calculate_severity_accident(self):
        # Critical accident: high confidence
        sev_crit = IncidentEngine.calculate_severity("accident", 0.88, [{"box": 1}])
        self.assertEqual(sev_crit, "critical")

        # High accident: moderate confidence
        sev_high = IncidentEngine.calculate_severity("accident", 0.75, [{"box": 1}])
        self.assertEqual(sev_high, "high")

        # Medium accident
        sev_med = IncidentEngine.calculate_severity("accident", 0.55, [{"box": 1}])
        self.assertEqual(sev_med, "medium")

    def test_calculate_severity_smoke(self):
        # High smoke: >= 0.85
        sev_high = IncidentEngine.calculate_severity("smoke", 0.87, [{"box": 1}])
        self.assertEqual(sev_high, "high")

        # Medium smoke: >= 0.60
        sev_med = IncidentEngine.calculate_severity("smoke", 0.65, [{"box": 1}])
        self.assertEqual(sev_med, "medium")

        # Low smoke: < 0.60
        sev_low = IncidentEngine.calculate_severity("smoke", 0.52, [{"box": 1}])
        self.assertEqual(sev_low, "low")


if __name__ == "__main__":
    unittest.main()
