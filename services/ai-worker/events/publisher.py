"""Event Publisher for AI Detections [M2].

Publishes AI detection candidates to Redis Streams ('ai:events') with HTTP fallback to the backend API.
"""

import json
import logging
from typing import Optional
import requests
import redis
from .event_schema import AIDetectionCandidate

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publishes AI event candidates to Redis Streams and/or Backend API."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        stream_key: str = "ai:events",
        api_url: Optional[str] = "http://localhost:8000"
    ):
        self.redis_url = redis_url
        self.stream_key = stream_key
        self.api_url = api_url.rstrip("/") if api_url else None
        self._redis_client: Optional[redis.Redis] = None

    @property
    def redis_client(self) -> Optional[redis.Redis]:
        if self._redis_client is None:
            try:
                self._redis_client = redis.Redis.from_url(self.redis_url, decode_responses=False)
                self._redis_client.ping()
                logger.info(f"Connected to Redis at {self.redis_url}")
            except Exception as e:
                logger.warning(f"Could not connect to Redis at {self.redis_url}: {e}")
                self._redis_client = None
        return self._redis_client

    def publish_to_stream(self, candidate: AIDetectionCandidate) -> Optional[str]:
        """Publishes the candidate to Redis Streams via XADD."""
        client = self.redis_client
        if client is not None:
            try:
                data = candidate.to_redis_dict()
                msg_id = client.xadd(self.stream_key, data)
                if isinstance(msg_id, bytes):
                    msg_id = msg_id.decode("utf-8")
                logger.info(
                    f"Published AI candidate {candidate.event_id} ({candidate.detection_type.value}) "
                    f"to stream '{self.stream_key}' with ID {msg_id}"
                )
                return msg_id
            except Exception as e:
                logger.error(f"Failed to publish to Redis stream '{self.stream_key}': {e}")
                self._redis_client = None
        return None

    def publish_to_api(self, candidate: AIDetectionCandidate) -> bool:
        """Sends candidate directly to Backend API /api/ai-detections/events via HTTP POST."""
        if not self.api_url:
            return False

        endpoint = f"{self.api_url}/api/ai-detections/events"
        try:
            payload = candidate.model_dump()
            response = requests.post(endpoint, json=payload, timeout=3.0)
            if response.status_code in (200, 201):
                logger.info(f"Delivered AI candidate {candidate.event_id} to API: {endpoint}")
                return True
            else:
                logger.warning(f"API returned status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            logger.debug(f"Direct API delivery to {endpoint} skipped or failed: {e}")
            return False

    def publish(self, candidate: AIDetectionCandidate) -> bool:
        """Attempts Redis Stream delivery first, falling back to / supplementing with direct API delivery."""
        stream_success = self.publish_to_stream(candidate) is not None
        api_success = self.publish_to_api(candidate)
        return stream_success or api_success
