"""Tests for Frame Preprocessing [M2]."""

import unittest
import numpy as np

try:
    import cv2
    from preprocessing.frame_processor import FrameProcessor
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


class TestFrameProcessor(unittest.TestCase):

    def setUp(self):
        if not HAS_CV2:
            self.skipTest("cv2 (OpenCV) is not installed in the host environment.")
        self.processor = FrameProcessor(target_size=(640, 640))

    def test_letterbox_shape(self):
        img = np.zeros((720, 1280, 3), dtype=np.uint8)
        boxed, ratio, (dw, dh) = self.processor.letterbox(img, new_shape=(640, 640), auto=False)

        self.assertEqual(boxed.shape, (640, 640, 3))
        self.assertGreater(ratio, 0.0)

    def test_coordinate_inversion(self):
        img_h, img_w = 720, 1280
        img = np.zeros((img_h, img_w, 3), dtype=np.uint8)
        _, ratio, pad = self.processor.letterbox(img, new_shape=(640, 640), auto=False)

        box_letter = (100.0, 150.0, 300.0, 400.0)
        x1, y1, x2, y2 = self.processor.scale_coords_to_original(
            box_letter, (img_h, img_w), ratio, pad
        )

        self.assertGreaterEqual(x1, 0.0)
        self.assertLessEqual(x2, img_w)
        self.assertGreaterEqual(y1, 0.0)
        self.assertLessEqual(y2, img_h)

    def test_normalization(self):
        frame = np.full((100, 100, 3), 255, dtype=np.uint8)
        norm = self.processor.normalize(frame)
        self.assertEqual(norm.dtype, np.float32)
        self.assertAlmostEqual(float(norm.max()), 1.0)
        self.assertAlmostEqual(float(norm.min()), 1.0)


if __name__ == "__main__":
    unittest.main()
