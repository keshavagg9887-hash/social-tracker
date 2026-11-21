"""Frame Preprocessing Module [M2].

Provides letterboxing, color transforms, normalization, and coordinate scaling for YOLO/CV detectors.
"""

from typing import Tuple, List, Optional
import cv2
import numpy as np


class FrameProcessor:
    """Standardized image preprocessing utilities for vision pipelines."""

    def __init__(self, target_size: Tuple[int, int] = (640, 640)):
        self.target_size = target_size

    def letterbox(
        self,
        img: np.ndarray,
        new_shape: Optional[Tuple[int, int]] = None,
        color: Tuple[int, int, int] = (114, 114, 114),
        auto: bool = True,
        scaleup: bool = True,
        stride: int = 32
    ) -> Tuple[np.ndarray, float, Tuple[float, float]]:
        """Resize and pad image while meeting stride-multiple constraints (YOLO standard letterbox)."""
        shape = img.shape[:2]  # current shape [height, width]
        new_shape = new_shape or self.target_size

        # Scale ratio (new / old)
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
        if not scaleup:  # only scale down, do not scale up (for better val mAP)
            r = min(r, 1.0)

        # Compute padding
        new_unpad = (int(round(shape[1] * r)), int(round(shape[0] * r)))
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding

        if auto:  # minimum rectangle
            dw, dh = np.mod(dw, stride), np.mod(dh, stride)

        dw /= 2  # divide padding into 2 sides
        dh /= 2

        if shape[::-1] != new_unpad:  # resize
            img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)

        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)

        return img, r, (dw, dh)

    def to_rgb(self, frame: np.ndarray) -> np.ndarray:
        """Converts BGR OpenCV frame to RGB."""
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def normalize(self, frame: np.ndarray) -> np.ndarray:
        """Normalizes frame pixel values to [0.0, 1.0] float32."""
        return frame.astype(np.float32) / 255.0

    def scale_coords_to_original(
        self,
        box: Tuple[float, float, float, float],
        orig_shape: Tuple[int, int],
        ratio: float,
        pad: Tuple[float, float]
    ) -> Tuple[float, float, float, float]:
        """Maps coordinates from letterboxed image back to original image dimensions."""
        x1, y1, x2, y2 = box
        dw, dh = pad

        # Remove padding
        x1 = (x1 - dw) / ratio
        y1 = (y1 - dh) / ratio
        x2 = (x2 - dw) / ratio
        y2 = (y2 - dh) / ratio

        # Clip to original frame boundaries
        h_orig, w_orig = orig_shape
        x1 = max(0.0, min(float(w_orig), x1))
        y1 = max(0.0, min(float(h_orig), y1))
        x2 = max(0.0, min(float(w_orig), x2))
        y2 = max(0.0, min(float(h_orig), y2))

        return x1, y1, x2, y2

    def apply_roi(self, frame: np.ndarray, polygon: List[Tuple[int, int]]) -> np.ndarray:
        """Applies a polygonal Region Of Interest mask, blacking out irrelevant areas."""
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        pts = np.array(polygon, dtype=np.int32)
        cv2.fillPoly(mask, [pts], 255)
        return cv2.bitwise_and(frame, frame, mask=mask)
