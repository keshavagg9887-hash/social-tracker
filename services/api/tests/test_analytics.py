"""Analytics & Reporting Unit Tests [M3]."""

import unittest
from app.analytics.schemas import AnalyticsSummaryResponse, CameraAnalyticsResponse, CameraStatItem


class TestAnalyticsSchemas(unittest.TestCase):

    def test_analytics_summary_serialization(self):
        summary = AnalyticsSummaryResponse(
            totalIncidents=12,
            activeIncidents=4,
            resolvedIncidents=6,
            falseAlarms=2,
            byType={"fire": 5, "smoke": 3, "accident": 4},
            bySeverity={"critical": 2, "high": 4, "medium": 5, "low": 1},
            byStatus={"detected": 1, "reviewing": 1, "confirmed": 2, "resolved": 6, "rejected": 2},
            averageResolutionMinutes=18.5,
        )

        self.assertEqual(summary.totalIncidents, 12)
        self.assertEqual(summary.activeIncidents, 4)
        self.assertEqual(summary.falseAlarms, 2)
        self.assertEqual(summary.byType["fire"], 5)
        self.assertAlmostEqual(summary.averageResolutionMinutes, 18.5)

    def test_camera_analytics_serialization(self):
        stats = CameraAnalyticsResponse(
            cameras=[
                CameraStatItem(
                    cameraId="cam-intersection-4",
                    incidentCount=7,
                    activeCount=2,
                    lastIncidentAt="2026-11-21T10:30:00Z",
                )
            ]
        )

        self.assertEqual(len(stats.cameras), 1)
        self.assertEqual(stats.cameras[0].cameraId, "cam-intersection-4")
        self.assertEqual(stats.cameras[0].incidentCount, 7)


if __name__ == "__main__":
    unittest.main()
