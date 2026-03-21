"""Celery worker configuration and task definitions."""

import os
from typing import Dict, Any

from celery import Celery

from src.tasks.pipeline import FeedbackPipeline
from src.utils.logger import get_app_logger

logger = get_app_logger()

# ---------------------------------------------------------------------------
# Celery app configuration
# ---------------------------------------------------------------------------

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "feedback_router",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# ---------------------------------------------------------------------------
# Shared pipeline instance (created lazily on first use per worker process)
# ---------------------------------------------------------------------------

_pipeline: FeedbackPipeline | None = None


def _get_pipeline() -> FeedbackPipeline:
    """Return a lazily-initialised FeedbackPipeline singleton."""
    global _pipeline
    if _pipeline is None:
        _pipeline = FeedbackPipeline()
    return _pipeline


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


@celery_app.task(name="feedback.process", bind=True, max_retries=3)
def process_feedback(self, raw_feedback: Dict[str, Any], channel: str) -> Dict[str, Any]:
    """Process raw feedback through the full pipeline.

    Runs intake, classification, routing, and response generation.

    Args:
        raw_feedback: Raw feedback data dict from the source channel.
        channel: Source channel identifier (e.g. "slack", "email").

    Returns:
        Serialised FeedbackItem dict with all fields populated.
    """
    try:
        logger.info(
            "Processing feedback via Celery",
            channel=channel,
        )

        pipeline = _get_pipeline()
        feedback_item = pipeline.process(raw_feedback, channel)

        result = feedback_item.model_dump(mode="json")

        logger.info(
            "Feedback processed successfully",
            feedback_id=feedback_item.id,
            status=feedback_item.lifecycle.status.value,
        )

        return result

    except Exception as exc:
        logger.error(
            "Error processing feedback in Celery task",
            exception=exc,
            channel=channel,
        )
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@celery_app.task(name="feedback.send_slack_notification", bind=True, max_retries=3)
def send_slack_notification(
    self,
    channel_id: str,
    message: Dict[str, Any],
) -> Dict[str, Any]:
    """Send a notification message to a Slack channel.

    Uses the Slack SDK to post a message. The SLACK_BOT_TOKEN environment
    variable must be set for this to succeed.

    Args:
        channel_id: Slack channel ID to post to.
        message: Message payload dict. May contain "text" and/or "blocks".

    Returns:
        Dict with delivery status and metadata.
    """
    try:
        from slack_sdk import WebClient
        from slack_sdk.errors import SlackApiError

        token = os.environ.get("SLACK_BOT_TOKEN")
        if not token:
            logger.warning("SLACK_BOT_TOKEN not set; skipping notification")
            return {"ok": False, "error": "SLACK_BOT_TOKEN not configured"}

        client = WebClient(token=token)

        response = client.chat_postMessage(
            channel=channel_id,
            text=message.get("text", ""),
            blocks=message.get("blocks"),
        )

        logger.info(
            "Slack notification sent",
            channel_id=channel_id,
            ts=response.get("ts"),
        )

        return {
            "ok": True,
            "channel": channel_id,
            "ts": response.get("ts"),
        }

    except Exception as exc:
        logger.error(
            "Error sending Slack notification",
            exception=exc,
            channel_id=channel_id,
        )
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@celery_app.task(name="feedback.generate_daily_digest")
def generate_daily_digest() -> Dict[str, Any]:
    """Generate and distribute the daily feedback digest.

    This is a placeholder implementation. In production it would:
      1. Query the database for the last 24 hours of feedback items.
      2. Compute aggregate statistics (counts, sentiment averages, etc.).
      3. Build a rich Slack message via SlackBlockBuilder.build_daily_digest.
      4. Post the digest to the configured digest channel.

    Returns:
        Dict with digest metadata and stats.
    """
    logger.info("Generating daily feedback digest")

    # Placeholder stats -- replace with real DB queries
    stats = {
        "total": 0,
        "escalations": 0,
        "avg_sentiment": "N/A",
        "pending": 0,
        "top_categories": {},
        "generated_at": __import__("datetime").datetime.utcnow().isoformat(),
    }

    logger.info("Daily digest generated", stats=stats)

    return {
        "status": "generated",
        "stats": stats,
    }
