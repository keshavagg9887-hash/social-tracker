"""AI Worker Entrypoint & Stream Processing Pipeline [M2].

Continuously ingests video feeds, samples frames, executes Fire, Smoke, and Accident detectors,
generates visual evidence snapshots, and publishes event candidates to Redis Streams & Backend API.
"""

import os
import sys
import time
import signal
import logging
from typing import Dict, List, Optional
import numpy as np

from ingestion.stream_reader import StreamReader
from preprocessing.frame_processor import FrameProcessor
from detectors.fire.fire_detector import FireDetector
from detectors.smoke.smoke_detector import SmokeDetector
from detectors.accident.accident_detector import AccidentDetector
from detectors.base import DetectionResult
from events.event_schema import AIDetectionCandidate, BoundingBox, DetectionType
from events.evidence_manager import EvidenceManager
from events.publisher import EventPublisher

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("AIWorker")


class AIWorkerPipeline:
    """End-to-end AI monitoring pipeline for camera streams."""

    def __init__(self):
        # Configuration from environment
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.stream_key = os.getenv("STREAM_KEY", "ai:events")
        self.api_url = os.getenv("API_URL", "http://localhost:8000")
        self.rtsp_base_url = os.getenv("MEDIAMTX_RTSP_URL", "rtsp://localhost:8554").rstrip("/")
        self.evidence_dir = os.getenv("EVIDENCE_DIR", "evidence")
        self.confidence_threshold = float(os.getenv("DETECTION_CONFIDENCE_THRESHOLD", "0.50"))
        self.sample_fps = float(os.getenv("SAMPLE_FPS", "3.0"))
        self.candidate_cooldown_sec = float(os.getenv("CANDIDATE_COOLDOWN_SEC", "5.0"))

        # Camera list to monitor
        raw_cameras = os.getenv("CAMERA_IDS", "cam_01")
        self.camera_ids = [c.strip() for c in raw_cameras.split(",") if c.strip()]

        # Initialize pipeline components
        self.processor = FrameProcessor(target_size=(640, 640))
        self.evidence_mgr = EvidenceManager(base_storage_dir=self.evidence_dir)
        self.publisher = EventPublisher(
            redis_url=self.redis_url,
            stream_key=self.stream_key,
            api_url=self.api_url
        )

        # Detectors
        self.fire_detector = FireDetector(confidence_threshold=self.confidence_threshold)
        self.smoke_detector = SmokeDetector(confidence_threshold=self.confidence_threshold)
        self.accident_detector = AccidentDetector(confidence_threshold=self.confidence_threshold)

        # Readers and state tracking
        self.readers: Dict[str, StreamReader] = {}
        self.last_candidate_time: Dict[str, float] = {}  # key: f"{camera_id}:{detection_type}"
        self.running = False

    def _get_stream_url(self, camera_id: str) -> str:
        """Determines the full stream URL for a given camera ID."""
        override = os.getenv(f"CAMERA_URL_{camera_id.upper()}")
        if override:
            return override
        return f"{self.rtsp_base_url}/{camera_id}"

    def start(self):
        """Starts stream ingestion and runs the main detection loop."""
        self.running = True
        logger.info("Initializing Social Empowerment Platform - AI Worker [M2]...")
        logger.info(f"Target sample FPS: {self.sample_fps} | Confidence threshold: {self.confidence_threshold}")
        logger.info(f"Redis target: {self.redis_url} -> '{self.stream_key}' | API: {self.api_url}")
        logger.info(f"Monitoring cameras: {self.camera_ids}")

        # Start stream readers for all configured cameras
        for cam_id in self.camera_ids:
            source_url = self._get_stream_url(cam_id)
            reader = StreamReader(
                stream_source=source_url,
                camera_id=cam_id,
                target_sample_fps=self.sample_fps
            )
            reader.start()
            self.readers[cam_id] = reader

        try:
            self._main_loop()
        finally:
            self.stop()

    def stop(self):
        """Stops all readers and cleans up resources."""
        self.running = False
        logger.info("Stopping AI Worker pipeline...")
        for cam_id, reader in self.readers.items():
            reader.stop()
        self.readers.clear()
        logger.info("AI Worker stopped successfully.")

    def _is_cooling_down(self, camera_id: str, det_type: str) -> bool:
        """Rate limits candidate generation per camera and type to prevent event flooding."""
        key = f"{camera_id}:{det_type}"
        last_time = self.last_candidate_time.get(key, 0.0)
        return (time.time() - last_time) < self.candidate_cooldown_sec

    def _mark_candidate_dispatched(self, camera_id: str, det_type: str):
        key = f"{camera_id}:{det_type}"
        self.last_candidate_time[key] = time.time()

    def process_frame_for_camera(self, camera_id: str, frame: np.ndarray):
        """Executes detectors on a sampled frame and dispatches candidates."""
        h, w = frame.shape[:2]

        # 1. Fire Detection
        fire_dets = self.fire_detector.detect(frame)
        if fire_dets and not self._is_cooling_down(camera_id, "fire"):
            self._handle_detection(camera_id, DetectionType.FIRE, fire_dets, frame)

        # 2. Smoke Detection
        smoke_dets = self.smoke_detector.detect(frame)
        if smoke_dets and not self._is_cooling_down(camera_id, "smoke"):
            self._handle_detection(camera_id, DetectionType.SMOKE, smoke_dets, frame)

        # 3. Road Accident Detection
        accident_dets = self.accident_detector.detect(frame)
        if accident_dets and not self._is_cooling_down(camera_id, "accident"):
            self._handle_detection(camera_id, DetectionType.ACCIDENT, accident_dets, frame)

    def _handle_detection(
        self,
        camera_id: str,
        detection_type: DetectionType,
        detections: List[DetectionResult],
        frame: np.ndarray
    ):
        """Packages detection into an event candidate, stores evidence snapshot, and publishes."""
        max_conf = max(d.confidence for d in detections)
        if max_conf < self.confidence_threshold:
            return

        # Map to standard BoundingBox schema
        boxes: List[BoundingBox] = []
        for d in detections:
            boxes.append(
                BoundingBox(
                    x1=d.bbox[0],
                    y1=d.bbox[1],
                    x2=d.bbox[2],
                    y2=d.bbox[3],
                    confidence=d.confidence,
                    label=d.label,
                    tracker_id=d.tracker_id
                )
            )

        # Create unique candidate event ID
        from uuid import uuid4
        event_id = str(uuid4())

        # Save visual evidence snapshot
        evidence_uri = self.evidence_mgr.save_snapshot(
            frame=frame,
            event_id=event_id,
            camera_id=camera_id,
            detection_type=detection_type.value,
            bounding_boxes=boxes,
            draw_annotations=True
        )

        candidate = AIDetectionCandidate(
            event_id=event_id,
            detection_type=detection_type,
            confidence=max_conf,
            camera_id=camera_id,
            location_reference=f"Registered Camera {camera_id}",
            evidence_reference=evidence_uri,
            bounding_boxes=boxes,
            metadata={
                "detector_count": len(detections),
                "resolution": f"{frame.shape[1]}x{frame.shape[0]}",
                "first_det_metadata": detections[0].metadata if detections else {}
            }
        )

        # Publish candidate to Redis Streams & Backend API
        dispatched = self.publisher.publish(candidate)
        if dispatched:
            self._mark_candidate_dispatched(camera_id, detection_type.value)
            logger.info(
                f"[EVENT CANDIDATE] {detection_type.value.upper()} on {camera_id} "
                f"(conf={max_conf:.2f}, id={event_id}) -> {evidence_uri}"
            )

    def _main_loop(self):
        """Active loop iterating across stream readers."""
        while self.running:
            active_count = 0
            for cam_id, reader in self.readers.items():
                if reader.should_sample():
                    ret, frame = reader.get_frame(timeout=0.05)
                    if ret and frame is not None:
                        active_count += 1
                        try:
                            self.process_frame_for_camera(cam_id, frame)
                        except Exception as e:
                            logger.error(f"Error processing frame for camera {cam_id}: {e}", exc_info=True)

            # Sleep briefly to yield CPU
            time.sleep(0.01)


def main():
    pipeline = AIWorkerPipeline()

    # Graceful shutdown handlers
    def handle_signal(sig, frame):
        logger.info(f"Received shutdown signal {sig}. Exiting...")
        pipeline.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    pipeline.start()


if __name__ == "__main__":
    main()
