"""Redis Stream Consumer for AI Detection Candidates [M3].

Asynchronously listens to the Redis stream ('ai:events') published by M2's AI Worker,
processes event candidates through the Incident Engine, and acknowledges stream entries.
"""

import asyncio
import json
import logging
from typing import Optional
import redis.asyncio as aioredis

from ..config import settings
from ..database.session import AsyncSessionLocal
from .engine import IncidentEngine

logger = logging.getLogger(__name__)


class RedisIncidentConsumer:
    """Consumes AI detection candidates from Redis Streams."""

    def __init__(self):
        self.stream_key = settings.REDIS_STREAM_AI_EVENTS
        self.group_name = settings.REDIS_CONSUMER_GROUP
        self.consumer_name = settings.REDIS_CONSUMER_NAME
        self.running = False
        self._task: Optional[asyncio.Task] = None

    async def _init_stream(self, client: aioredis.Redis) -> None:
        """Ensure consumer group exists on the stream."""
        try:
            await client.xgroup_create(
                name=self.stream_key,
                groupname=self.group_name,
                id="$",
                mkstream=True,
            )
            logger.info(f"Created Redis stream consumer group '{self.group_name}' on '{self.stream_key}'")
        except aioredis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group '{self.group_name}' already exists.")
            else:
                logger.warning(f"Consumer group init notice: {e}")

    async def start(self) -> None:
        """Start async consumer loop in the background."""
        self.running = True
        self._task = asyncio.create_task(self._consume_loop())
        logger.info("[Redis Consumer] Started background worker for AI events.")

    async def stop(self) -> None:
        """Gracefully stop consumer loop."""
        self.running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[Redis Consumer] Stopped background worker.")

    async def _consume_loop(self) -> None:
        """Main loop consuming candidate messages."""
        while self.running:
            client: Optional[aioredis.Redis] = None
            try:
                client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                await self._init_stream(client)

                while self.running:
                    try:
                        # Read new messages with 2 second block
                        streams = {self.stream_key: ">"}
                        entries = await client.xreadgroup(
                            groupname=self.group_name,
                            consumername=self.consumer_name,
                            streams=streams,
                            count=10,
                            block=2000,
                        )

                        if not entries:
                            await asyncio.sleep(0.5)
                            continue

                        for stream_name, messages in entries:
                            for message_id, data in messages:
                                await self._handle_message(client, message_id, data)

                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        logger.error(f"[Redis Consumer] Error reading stream: {e}")
                        await asyncio.sleep(2)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[Redis Consumer] Redis connection failed, retrying in 5s: {e}")
                await asyncio.sleep(5)
            finally:
                if client:
                    await client.aclose()

    async def _handle_message(
        self,
        client: aioredis.Redis,
        message_id: str,
        data: dict,
    ) -> None:
        """Process a single event candidate message and acknowledge."""
        try:
            # Parse bounding boxes and metadata if serialized
            boxes_raw = data.get("bounding_boxes", "[]")
            meta_raw = data.get("metadata", "{}")

            boxes = json.loads(boxes_raw) if isinstance(boxes_raw, str) else boxes_raw
            meta = json.loads(meta_raw) if isinstance(meta_raw, str) else meta_raw

            candidate = {
                "event_id": data.get("event_id"),
                "detection_type": data.get("detection_type"),
                "confidence": float(data.get("confidence", 0.0)),
                "timestamp": data.get("timestamp"),
                "camera_id": data.get("camera_id"),
                "location_reference": data.get("location_reference"),
                "evidence_reference": data.get("evidence_reference"),
                "bounding_boxes": boxes,
                "metadata": meta,
            }

            async with AsyncSessionLocal() as session:
                await IncidentEngine.process_candidate(session, candidate)

            # Acknowledge message in Redis stream
            await client.xack(self.stream_key, self.group_name, message_id)

        except Exception as e:
            logger.error(f"[Redis Consumer] Failed to process message {message_id}: {e}")


redis_consumer = RedisIncidentConsumer()
