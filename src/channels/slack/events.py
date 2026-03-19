"""Slack event handlers for feedback ingestion."""

from typing import Dict, Any, Optional, List
from src.agents.intake import IntakeAgent
from src.schemas.feedback import FeedbackItem


class SlackEventHandler:
    """Handles Slack events for feedback."""

    # Channels to monitor for feedback
    FEEDBACK_CHANNELS = [
        "feedback",
        "feature-requests",
        "bugs",
        "complaints",
        "customer-feedback",
        "support",
    ]

    def __init__(self, intake_agent: Optional[IntakeAgent] = None,
                 monitored_channels: Optional[List[str]] = None):
        """Initialize Slack event handler.

        Args:
            intake_agent: Intake agent for normalizing feedback
            monitored_channels: List of channel IDs or names to monitor
        """
        self.intake_agent = intake_agent or IntakeAgent()
        self.monitored_channels = monitored_channels or self.FEEDBACK_CHANNELS

    def should_process_event(self, channel_id: str, channel_name: Optional[str] = None) -> bool:
        """Determine if event should be processed.

        Args:
            channel_id: Slack channel ID
            channel_name: Slack channel name

        Returns:
            True if event should be processed
        """
        return (channel_id in self.monitored_channels or
                (channel_name and channel_name.lower() in self.monitored_channels))

    def handle_message_event(self, event_data: Dict[str, Any]) -> Optional[FeedbackItem]:
        """Handle Slack message event.

        Args:
            event_data: Slack message event data

        Returns:
            FeedbackItem if event is feedback, None otherwise
        """
        channel_id = event_data.get("channel")
        channel_name = event_data.get("channel_name")

        # Check if we should process this channel
        if not self.should_process_event(channel_id, channel_name):
            return None

        # Ignore bot messages and edits
        if event_data.get("bot_id") or event_data.get("subtype") == "message_changed":
            return None

        # Extract message data
        message_data = {
            "ts": event_data.get("ts"),
            "text": event_data.get("text", ""),
            "user": event_data.get("user"),
            "channel": channel_id,
            "thread_ts": event_data.get("thread_ts"),
            "reactions": event_data.get("reactions", []),
        }

        return self.intake_agent.normalize_slack_message(message_data)

    def handle_app_mention(self, event_data: Dict[str, Any]) -> Optional[FeedbackItem]:
        """Handle app mention event.

        Args:
            event_data: Slack mention event data

        Returns:
            FeedbackItem if mention is feedback
        """
        text = event_data.get("text", "")

        # Remove app mention from text
        cleaned_text = text.replace("<@", "").replace(">", "").split(">", 1)[-1].strip()

        message_data = {
            "ts": event_data.get("ts"),
            "text": cleaned_text,
            "user": event_data.get("user"),
            "channel": event_data.get("channel"),
            "thread_ts": event_data.get("thread_ts"),
            "reactions": event_data.get("reactions", []),
        }

        return self.intake_agent.normalize_slack_message(message_data)

    def handle_reaction_added(self, event_data: Dict[str, Any]) -> Optional[FeedbackItem]:
        """Handle reaction added event (sentiment indicator).

        Args:
            event_data: Slack reaction event data

        Returns:
            FeedbackItem if reaction indicates feedback
        """
        reaction = event_data.get("reaction", "").lower()

        # Map reactions to feedback sentiment
        negative_reactions = ["thumbsdown", "-1", "x", "sad", "poop", "fire", "rage"]
        positive_reactions = ["thumbsup", "+1", "heart", "tada", "rocket", "tada"]

        if reaction not in negative_reactions + positive_reactions:
            return None

        # Create feedback from reaction context
        message_data = {
            "ts": event_data.get("item", {}).get("ts"),
            "text": f"[Reaction: {reaction}] on message",
            "user": event_data.get("user"),
            "channel": event_data.get("item", {}).get("channel"),
            "thread_ts": None,
            "reactions": [reaction],
        }

        return self.intake_agent.normalize_slack_message(message_data)

    def get_channel_config(self) -> Dict[str, Dict[str, Any]]:
        """Get configuration for monitored channels.

        Returns:
            Dictionary of channel configurations
        """
        return {
            "feedback": {
                "description": "General feedback channel",
                "priority": "normal",
                "auto_process": True,
            },
            "feature-requests": {
                "description": "Feature requests",
                "priority": "normal",
                "auto_process": True,
            },
            "bugs": {
                "description": "Bug reports",
                "priority": "high",
                "auto_process": True,
            },
            "complaints": {
                "description": "Complaints and concerns",
                "priority": "high",
                "auto_process": True,
            },
            "customer-feedback": {
                "description": "Customer feedback",
                "priority": "high",
                "auto_process": True,
            },
            "support": {
                "description": "Support requests",
                "priority": "critical",
                "auto_process": True,
            },
        }
