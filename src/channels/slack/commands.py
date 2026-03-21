"""Slack slash command handlers for feedback management."""

from typing import Dict, Any, List
from datetime import datetime

from src.channels.slack.blocks import SlackBlockBuilder


class SlackCommandHandler:
    """Handles Slack slash commands for feedback operations."""

    # Valid teams for assignment
    VALID_TEAMS = [
        "engineering", "product", "sales", "support",
        "customer-success", "leadership", "marketing",
    ]

    def __init__(self):
        """Initialize the slash command handler."""
        self.block_builder = SlackBlockBuilder()

    def handle_command(self, command: str, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch a slash command to the appropriate handler.

        Args:
            command: The slash command name (e.g. "/feedback-status")
            command_data: Slack command payload containing text, user_id,
                          channel_id, response_url, etc.

        Returns:
            Response dict with response_type and text/blocks for Slack.
        """
        handlers = {
            "/feedback-status": self.handle_status,
            "/feedback-assign": self.handle_assign,
            "/feedback-escalate": self.handle_escalate,
            "/feedback-resolve": self.handle_resolve,
            "/feedback-digest": self.handle_digest,
        }

        handler = handlers.get(command)
        if not handler:
            return {
                "response_type": "ephemeral",
                "text": f"Unknown command: {command}. "
                        f"Available commands: {', '.join(handlers.keys())}",
            }

        return handler(command_data)

    def handle_status(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle /feedback-status [feedback_id].

        Returns the current status of a feedback item including classification,
        routing assignment, and lifecycle state.

        Args:
            command_data: Slack command payload. Expected text format:
                          "<feedback_id>"

        Returns:
            Ephemeral response with feedback status details.
        """
        text = (command_data.get("text") or "").strip()
        user_id = command_data.get("user_id", "unknown")

        if not text:
            return {
                "response_type": "ephemeral",
                "text": "Usage: `/feedback-status <feedback_id>`\n"
                        "Example: `/feedback-status fb_abc123def456`",
            }

        feedback_id = text.split()[0]

        # Placeholder: in production this would query the database
        # For now, return structured placeholder data showing the format
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Feedback Status: {feedback_id}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Feedback ID:*\n`{feedback_id}`",
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Status:*\nrouted",
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Category:*\nbug",
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Sentiment:*\nnegative (0.75)",
                    },
                ],
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*Assigned Team:*\nengineering",
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Priority:*\n2",
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Escalated:*\nNo",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Requested by:*\n<@{user_id}>",
                    },
                ],
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Looked up at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
                    },
                ],
            },
        ]

        return {
            "response_type": "ephemeral",
            "blocks": blocks,
        }

    def handle_assign(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle /feedback-assign [feedback_id] [team].

        Assigns a feedback item to a specific team for handling.

        Args:
            command_data: Slack command payload. Expected text format:
                          "<feedback_id> <team>"

        Returns:
            In-channel response confirming the assignment.
        """
        text = (command_data.get("text") or "").strip()
        user_id = command_data.get("user_id", "unknown")

        parts = text.split()
        if len(parts) < 2:
            return {
                "response_type": "ephemeral",
                "text": "Usage: `/feedback-assign <feedback_id> <team>`\n"
                        f"Available teams: {', '.join(self.VALID_TEAMS)}\n"
                        "Example: `/feedback-assign fb_abc123def456 engineering`",
            }

        feedback_id = parts[0]
        team = parts[1].lower()

        if team not in self.VALID_TEAMS:
            return {
                "response_type": "ephemeral",
                "text": f"Unknown team: `{team}`\n"
                        f"Available teams: {', '.join(self.VALID_TEAMS)}",
            }

        # Placeholder: in production this would update the database
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":arrow_right: *Feedback Assigned*\n"
                            f"<@{user_id}> assigned `{feedback_id}` to *{team}* team.",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Assigned at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
                    },
                ],
            },
        ]

        return {
            "response_type": "in_channel",
            "blocks": blocks,
        }

    def handle_escalate(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle /feedback-escalate [feedback_id] [reason].

        Escalates a feedback item with a reason, notifying the team.

        Args:
            command_data: Slack command payload. Expected text format:
                          "<feedback_id> <reason ...>"

        Returns:
            In-channel response with escalation alert.
        """
        text = (command_data.get("text") or "").strip()
        user_id = command_data.get("user_id", "unknown")

        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return {
                "response_type": "ephemeral",
                "text": "Usage: `/feedback-escalate <feedback_id> <reason>`\n"
                        "Example: `/feedback-escalate fb_abc123def456 "
                        "Customer threatening to churn`",
            }

        feedback_id = parts[0]
        reason = parts[1]

        # Placeholder: in production this would update the database and
        # trigger notifications via the escalation engine
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "ESCALATION ALERT",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Feedback ID:*\n`{feedback_id}`",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Escalated by:*\n<@{user_id}>",
                    },
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Reason:*\n{reason}",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Escalated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
                    },
                ],
            },
        ]

        return {
            "response_type": "in_channel",
            "blocks": blocks,
        }

    def handle_resolve(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle /feedback-resolve [feedback_id].

        Marks a feedback item as resolved and closes its lifecycle.

        Args:
            command_data: Slack command payload. Expected text format:
                          "<feedback_id>"

        Returns:
            In-channel response confirming resolution.
        """
        text = (command_data.get("text") or "").strip()
        user_id = command_data.get("user_id", "unknown")

        if not text:
            return {
                "response_type": "ephemeral",
                "text": "Usage: `/feedback-resolve <feedback_id>`\n"
                        "Example: `/feedback-resolve fb_abc123def456`",
            }

        feedback_id = text.split()[0]

        # Placeholder: in production this would update the database
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":white_check_mark: *Feedback Resolved*\n"
                            f"<@{user_id}> resolved `{feedback_id}`.",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Resolved at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
                    },
                ],
            },
        ]

        return {
            "response_type": "in_channel",
            "blocks": blocks,
        }

    def handle_digest(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle /feedback-digest.

        Returns a daily summary of feedback statistics using the
        SlackBlockBuilder's daily digest format.

        Args:
            command_data: Slack command payload (text is ignored for digest).

        Returns:
            Ephemeral response with daily digest blocks.
        """
        # Placeholder stats: in production these come from the database
        stats = {
            "total": 42,
            "escalations": 3,
            "avg_sentiment": "neutral (0.52)",
            "pending": 7,
            "top_categories": {
                "bug": 14,
                "feature": 11,
                "question": 8,
                "complaint": 5,
                "praise": 4,
            },
        }

        # Use SlackBlockBuilder for the rich digest format.
        # Pass an empty list for feedback_items since we don't have DB access.
        digest_message = SlackBlockBuilder.build_daily_digest(
            feedback_items=[],
            stats=stats,
        )

        return {
            "response_type": "ephemeral",
            "blocks": digest_message["blocks"],
        }
