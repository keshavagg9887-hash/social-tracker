"""Notification Worker - Alert Dispatcher Service [M3].

Listens to the Redis Stream ('sep:notifications') and dispatches real-time alerts
to emergency responders and incident handlers via Email (SMTP), Webhooks, and SMS Gateways.
"""

import asyncio
import json
import logging
import os
import signal
import sys
from typing import Optional
import aiosmtplib
from email.message import EmailMessage
import redis.asyncio as aioredis
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Notification Worker]: %(message)s",
)
logger = logging.getLogger("notification-worker")

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
STREAM_NAME = os.getenv("REDIS_STREAM_NOTIFICATIONS", "sep:notifications")
GROUP_NAME = os.getenv("NOTIFICATION_GROUP_NAME", "notification_dispatcher_group")
CONSUMER_NAME = os.getenv("NOTIFICATION_CONSUMER_NAME", f"worker_{os.getpid()}")

SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ALERT_RECIPIENT_EMAIL = os.getenv("ALERT_RECIPIENT_EMAIL", "alerts@socialtracker.org")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")


class NotificationDispatcher:
    """Consumes notification queue and dispatches alerts via configured communication channels."""

    def __init__(self):
        self.running = True

    async def send_email_alert(self, title: str, message_body: str, severity: str) -> bool:
        """Send email alert via SMTP if server is configured."""
        if not SMTP_SERVER or not SMTP_USER:
            logger.debug("SMTP not configured. Skipping email dispatch.")
            return False

        try:
            msg = EmailMessage()
            msg["Subject"] = f"[{severity.upper()}] SEP Incident Alert: {title}"
            msg["From"] = SMTP_USER
            msg["To"] = ALERT_RECIPIENT_EMAIL
            msg.set_content(
                f"Emergency Notification Alert\n\n"
                f"Severity: {severity.upper()}\n"
                f"Title: {title}\n\n"
                f"Details:\n{message_body}\n\n"
                f"-- Social Empowerment Platform Incident System"
            )

            await aiosmtplib.send(
                msg,
                hostname=SMTP_SERVER,
                port=SMTP_PORT,
                username=SMTP_USER,
                password=SMTP_PASSWORD,
                use_tls=SMTP_PORT == 465,
                start_tls=SMTP_PORT == 587,
            )
            logger.info(f"Dispatched email alert for '{title}' to {ALERT_RECIPIENT_EMAIL}")
            return True
        except Exception as e:
            logger.error(f"Failed to dispatch email alert: {e}")
            return False

    async def send_webhook_alert(self, data: dict) -> bool:
        """Forward alert to external webhook if configured."""
        if not WEBHOOK_URL:
            return False

        try:
            loop = asyncio.get_running_loop()
            resp = await loop.run_in_executor(
                None,
                lambda: requests.post(WEBHOOK_URL, json=data, timeout=4.0),
            )
            logger.info(f"Webhook alert dispatched to {WEBHOOK_URL} (status: {resp.status_code})")
            return resp.status_code < 400
        except Exception as e:
            logger.error(f"Webhook delivery failed to {WEBHOOK_URL}: {e}")
            return False

    async def dispatch(self, data: dict) -> None:
        """Main dispatch handler for a single notification payload."""
        title = data.get("title", "Incident Alert")
        msg = data.get("message", "")
        severity = data.get("severity", "medium").upper()
        channel = data.get("channel", "all")
        incident_id = data.get("incident_id", "N/A")

        # Terminal banner log
        border = "=" * 60
        logger.info(
            f"\n{border}\n"
            f" [ALERT DISPATCH] Severity: {severity}\n"
            f" Incident: {incident_id}\n"
            f" Title:    {title}\n"
            f" Channel:  {channel}\n"
            f" Message:  {msg}\n"
            f"{border}"
        )

        # Trigger external channels concurrently
        await asyncio.gather(
            self.send_email_alert(title, msg, severity),
            self.send_webhook_alert(data),
            return_exceptions=True,
        )

    async def run(self) -> None:
        """Continuous consumer loop listening to Redis notification stream."""
        logger.info(f"Connecting to Redis at {REDIS_URL}...")
        logger.info(f"Listening on stream '{STREAM_NAME}' as group '{GROUP_NAME}'...")

        while self.running:
            client: Optional[aioredis.Redis] = None
            try:
                client = aioredis.from_url(REDIS_URL, decode_responses=True)

                # Ensure stream and consumer group exist
                try:
                    await client.xgroup_create(
                        name=STREAM_NAME,
                        groupname=GROUP_NAME,
                        id="$",
                        mkstream=True,
                    )
                    logger.info(f"Created consumer group '{GROUP_NAME}' on stream '{STREAM_NAME}'")
                except aioredis.ResponseError as e:
                    if "BUSYGROUP" not in str(e):
                        logger.warning(f"Consumer group notice: {e}")

                while self.running:
                    try:
                        entries = await client.xreadgroup(
                            groupname=GROUP_NAME,
                            consumername=CONSUMER_NAME,
                            streams={STREAM_NAME: ">"},
                            count=10,
                            block=2000,
                        )

                        if not entries:
                            await asyncio.sleep(0.5)
                            continue

                        for stream, messages in entries:
                            for msg_id, payload in messages:
                                await self.dispatch(payload)
                                await client.xack(STREAM_NAME, GROUP_NAME, msg_id)

                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        logger.error(f"Error reading notification stream: {e}")
                        await asyncio.sleep(2)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Redis connection dropped, retrying in 5s: {e}")
                await asyncio.sleep(5)
            finally:
                if client:
                    await client.aclose()


async def main_async():
    dispatcher = NotificationDispatcher()

    # Graceful shutdown handler
    def shutdown():
        logger.info("Shutdown signal received. Stopping dispatcher...")
        dispatcher.running = False

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, shutdown)
        except NotImplementedError:
            # Signal handling on Windows
            pass

    await dispatcher.run()


def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Notification worker stopped.")


if __name__ == "__main__":
    main()
