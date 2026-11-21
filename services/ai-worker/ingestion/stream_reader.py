"""Stream Reader and Frame Ingestion Module [M2].

Handles video ingestion from RTSP streams, WebRTC proxies, video files, or webcams with non-blocking capture and frame sampling.
"""

import time
import queue
import threading
import logging
from typing import Optional, Tuple
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class StreamReader:
    """Threaded RTSP / video stream reader providing real-time frame access without buffer delay."""

    def __init__(
        self,
        stream_source: str,
        camera_id: str,
        target_sample_fps: float = 3.0,
        reconnect_delay_sec: float = 2.0,
    ):
        self.stream_source = stream_source
        self.camera_id = camera_id
        self.target_sample_fps = target_sample_fps
        self.reconnect_delay_sec = reconnect_delay_sec
        self.sample_interval = 1.0 / max(0.1, target_sample_fps)

        self._queue: queue.Queue = queue.Queue(maxsize=1)
        self._stopped = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_sample_time: float = 0.0
        self._is_connected: bool = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def start(self) -> "StreamReader":
        """Starts the background frame capture thread."""
        self._stopped.clear()
        self._thread = threading.Thread(target=self._capture_loop, name=f"StreamReader-{self.camera_id}", daemon=True)
        self._thread.start()
        logger.info(f"Started StreamReader for camera '{self.camera_id}' ({self.stream_source})")
        return self

    def stop(self) -> None:
        """Signals the capture thread to stop and waits for termination."""
        self._stopped.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._is_connected = False
        logger.info(f"Stopped StreamReader for camera '{self.camera_id}'")

    def _open_capture(self) -> Optional[cv2.VideoCapture]:
        """Attempts to open OpenCV VideoCapture for RTSP, file, or device."""
        source = int(self.stream_source) if str(self.stream_source).isdigit() else self.stream_source
        cap = cv2.VideoCapture(source)
        if isinstance(source, str) and source.startswith("rtsp://"):
            # Set minimal buffer size for RTSP to reduce latency
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if cap.isOpened():
            self._is_connected = True
            logger.info(f"Connected to stream source: {self.stream_source}")
            return cap
        self._is_connected = False
        logger.warning(f"Failed to open stream source: {self.stream_source}")
        return None

    def _capture_loop(self) -> None:
        """Worker thread loop reading frames continuously to prevent RTSP buffer lag."""
        cap: Optional[cv2.VideoCapture] = None

        while not self._stopped.is_set():
            if cap is None or not cap.isOpened():
                cap = self._open_capture()
                if cap is None:
                    time.sleep(self.reconnect_delay_sec)
                    continue

            ret, frame = cap.read()
            if not ret or frame is None:
                logger.warning(f"Stream '{self.camera_id}' disconnected or reached EOF. Reconnecting...")
                self._is_connected = False
                cap.release()
                cap = None
                time.sleep(self.reconnect_delay_sec)
                continue

            # Keep only the freshest frame in queue
            if not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    pass

            try:
                self._queue.put_nowait(frame)
            except queue.Full:
                pass

        if cap is not None:
            cap.release()

    def get_frame(self, timeout: float = 0.5) -> Tuple[bool, Optional[np.ndarray]]:
        """Retrieves the latest available frame from the capture queue."""
        try:
            frame = self._queue.get(timeout=timeout)
            return True, frame
        except queue.Empty:
            return False, None

    def should_sample(self) -> bool:
        """Determines if enough time has elapsed to process a frame at the target sampling FPS."""
        now = time.time()
        if now - self._last_sample_time >= self.sample_interval:
            self._last_sample_time = now
            return True
        return False
