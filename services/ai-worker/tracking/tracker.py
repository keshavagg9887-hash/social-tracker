"""Multi-Object Tracker Module [M2].

Lightweight and fast IoU tracker / ByteTrack-compatible tracking engine for vehicles and scene objects.
Tracks object centroids, speeds, and trajectories to enable accident and collision detection.
"""

from typing import List, Tuple, Dict, Optional
import numpy as np
try:
    from detectors.base import DetectionResult
except (ImportError, ValueError):
    from ..detectors.base import DetectionResult


def calculate_iou(boxA: Tuple[float, float, float, float], boxB: Tuple[float, float, float, float]) -> float:
    """Calculates Intersection over Union (IoU) between two bounding boxes (x1, y1, x2, y2)."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    inter_width = max(0.0, xB - xA)
    inter_height = max(0.0, yB - yA)
    inter_area = inter_width * inter_height

    boxA_area = max(0.0, (boxA[2] - boxA[0]) * (boxA[3] - boxA[0]))
    boxB_area = max(0.0, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))

    union_area = boxA_area + boxB_area - inter_area
    if union_area <= 0:
        return 0.0
    return inter_area / union_area


class Track:
    """Maintains state for a single tracked object over time."""

    def __init__(self, track_id: int, detection: DetectionResult):
        self.track_id = track_id
        self.label = detection.label
        self.bbox = detection.bbox
        self.confidence = detection.confidence
        self.hits = 1
        self.time_since_update = 0
        
        # History of centroids (x, y)
        cx = (detection.bbox[0] + detection.bbox[2]) / 2.0
        cy = (detection.bbox[1] + detection.bbox[3]) / 2.0
        self.trajectory: List[Tuple[float, float]] = [(cx, cy)]
        self.velocity: float = 0.0

    def update(self, detection: DetectionResult) -> None:
        """Updates track with a new matched detection."""
        self.bbox = detection.bbox
        self.confidence = detection.confidence
        self.hits += 1
        self.time_since_update = 0

        cx = (detection.bbox[0] + detection.bbox[2]) / 2.0
        cy = (detection.bbox[1] + detection.bbox[3]) / 2.0
        prev_cx, prev_cy = self.trajectory[-1]
        
        # Calculate instantaneous velocity (pixel distance)
        dist = np.sqrt((cx - prev_cx) ** 2 + (cy - prev_cy) ** 2)
        self.velocity = (self.velocity * 0.6) + (dist * 0.4)
        
        self.trajectory.append((cx, cy))
        if len(self.trajectory) > 30:
            self.trajectory.pop(0)

    def mark_missed(self) -> None:
        self.time_since_update += 1


class ObjectTracker:
    """Real-time Multi-Object Tracker assigning persistent IDs and monitoring velocities."""

    def __init__(self, iou_threshold: float = 0.3, max_age: int = 15, min_hits: int = 2):
        self.iou_threshold = iou_threshold
        self.max_age = max_age
        self.min_hits = min_hits
        self.tracks: Dict[int, Track] = {}
        self._next_id = 1

    def update(self, detections: List[DetectionResult]) -> List[DetectionResult]:
        """Matches detections against active tracks, assigns tracker IDs, and cleans up dead tracks."""
        unmatched_dets = list(range(len(detections)))
        unmatched_tracks = list(self.tracks.keys())
        matches: List[Tuple[int, int]] = []

        # Greedy IoU matching
        if self.tracks and detections:
            iou_matrix = np.zeros((len(self.tracks), len(detections)), dtype=np.float32)
            track_keys = list(self.tracks.keys())

            for i, tid in enumerate(track_keys):
                for j, det in enumerate(detections):
                    # Only match if labels match or both are vehicles
                    iou_matrix[i, j] = calculate_iou(self.tracks[tid].bbox, det.bbox)

            for _ in range(min(len(track_keys), len(detections))):
                max_idx = np.unravel_index(np.argmax(iou_matrix), iou_matrix.shape)
                i, j = max_idx
                max_iou = iou_matrix[i, j]
                if max_iou < self.iou_threshold:
                    break

                tid = track_keys[i]
                matches.append((tid, j))
                iou_matrix[i, :] = -1.0
                iou_matrix[:, j] = -1.0
                if tid in unmatched_tracks:
                    unmatched_tracks.remove(tid)
                if j in unmatched_dets:
                    unmatched_dets.remove(j)

        # Update matched tracks
        for tid, det_idx in matches:
            det = detections[det_idx]
            self.tracks[tid].update(det)
            det.tracker_id = tid

        # Handle unmatched active tracks
        for tid in unmatched_tracks:
            self.tracks[tid].mark_missed()

        # Delete expired tracks
        dead_tracks = [tid for tid, trk in self.tracks.items() if trk.time_since_update > self.max_age]
        for tid in dead_tracks:
            del self.tracks[tid]

        # Initialize new tracks for unmatched detections
        for det_idx in unmatched_dets:
            det = detections[det_idx]
            new_id = self._next_id
            self._next_id += 1
            self.tracks[new_id] = Track(new_id, det)
            det.tracker_id = new_id

        # Return updated detections with assigned tracker IDs
        return detections
