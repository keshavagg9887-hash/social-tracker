"""Evidence Manager for Storing AI Detection Snapshots [M2].

Handles saving and managing image frames with annotated bounding boxes for human review.
"""

import os
import cv2
import numpy as np
from datetime import datetime, timezone
from typing import List, Optional
from .event_schema import BoundingBox


class EvidenceManager:
    """Manages the creation and storage of visual evidence snapshots."""

    def __init__(self, base_storage_dir: str = "evidence", relative_url_prefix: str = "/evidence"):
        self.base_storage_dir = base_storage_dir
        self.relative_url_prefix = relative_url_prefix
        os.makedirs(self.base_storage_dir, exist_ok=True)

    def save_snapshot(
        self,
        frame: np.ndarray,
        event_id: str,
        camera_id: str,
        detection_type: str,
        bounding_boxes: Optional[List[BoundingBox]] = None,
        draw_annotations: bool = True
    ) -> str:
        """Annotates and saves an evidence frame to disk, returning its URI reference."""
        annotated_frame = frame.copy()
        
        # Color mapping by detection type (BGR)
        color_map = {
            "fire": (0, 0, 255),       # Red
            "smoke": (128, 128, 128),  # Gray
            "accident": (0, 140, 255), # Orange
        }
        primary_color = color_map.get(detection_type.lower(), (0, 255, 0))

        if draw_annotations and bounding_boxes:
            h, w = annotated_frame.shape[:2]
            for box in bounding_boxes:
                # If coords are normalized [0..1], scale to pixel coordinates
                x1 = int(box.x1 if box.x1 > 1.0 else box.x1 * w)
                y1 = int(box.y1 if box.y1 > 1.0 else box.y1 * h)
                x2 = int(box.x2 if box.x2 > 1.0 else box.x2 * w)
                y2 = int(box.y2 if box.y2 > 1.0 else box.y2 * h)

                # Draw bounding rectangle
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), primary_color, 2)

                # Prepare label text
                tracker_str = f" #{box.tracker_id}" if box.tracker_id is not None else ""
                label_text = f"{box.label}{tracker_str} ({box.confidence:.2f})"

                # Draw label background and text
                (tw, th), baseline = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(
                    annotated_frame,
                    (x1, max(0, y1 - th - baseline - 4)),
                    (x1 + tw + 4, max(th + 4, y1)),
                    primary_color,
                    -1
                )
                cv2.putText(
                    annotated_frame,
                    label_text,
                    (x1 + 2, max(th, y1 - 2)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA
                )

        # Add timestamp and watermark banner
        timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
        watermark = f"CAM: {camera_id} | {detection_type.upper()} | {timestamp_str}"
        cv2.putText(
            annotated_frame,
            watermark,
            (10, 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            3,
            cv2.LINE_AA
        )
        cv2.putText(
            annotated_frame,
            watermark,
            (10, 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        # Organize folder by date and camera
        date_folder = datetime.now(timezone.utc).strftime("%Y%m%d")
        camera_dir = os.path.join(self.base_storage_dir, date_folder, camera_id)
        os.makedirs(camera_dir, exist_ok=True)

        filename = f"{event_id}.jpg"
        file_path = os.path.join(camera_dir, filename)

        # Save JPEG with 85% quality
        cv2.imwrite(file_path, annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])

        # Return standardized URL path reference
        relative_path = f"{self.relative_url_prefix}/{date_folder}/{camera_id}/{filename}".replace("\\", "/")
        return relative_path
