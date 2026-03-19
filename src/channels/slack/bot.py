"""Slack bot core functionality."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class BotConfig:
    """Slack bot configuration."""
    name: str = "Feedback Router Bot"
    emoji: str = ":robot_face:"
    greeting: str = "Hi there! I'm your feedback routing assistant."
    signature: str = "Feedback Router"

    # Personality
    tone: str = "professional_and_friendly"
    show_thinking: bool = True
    acknowledge_confusion: bool = True

    # Behavior
    thread_replies: bool = True
    dnd_aware: bool = True
    typing_indicator: bool = True


class ThreadStatusTracker:
    """Tracks feedback status in Slack threads."""

    def __init__(self):
        """Initialize thread tracker."""
        self.threads: Dict[str, Dict[str, Any]] = {}

    def start_thread(self, thread_ts: str, feedback_id: str, metadata: Dict[str, Any]) -> None:
        """Start tracking thread for feedback.

        Args:
            thread_ts: Slack thread timestamp
            feedback_id: Feedback ID
            metadata: Thread metadata
        """
        self.threads[thread_ts] = {
            "feedback_id": feedback_id,
            "started_at": datetime.utcnow(),
            "status": "opened",
            "messages": [],
            **metadata
        }

    def update_status(self, thread_ts: str, status: str, message: str = "") -> None:
        """Update thread status.

        Args:
            thread_ts: Slack thread timestamp
            status: New status
            message: Optional status message
        """
        if thread_ts in self.threads:
            self.threads[thread_ts]["status"] = status
            if message:
                self.threads[thread_ts]["messages"].append({
                    "timestamp": datetime.utcnow(),
                    "message": message
                })

    def get_thread_status(self, thread_ts: str) -> Optional[Dict[str, Any]]:
        """Get thread status.

        Args:
            thread_ts: Slack thread timestamp

        Returns:
            Thread status if tracking
        """
        return self.threads.get(thread_ts)

    def close_thread(self, thread_ts: str) -> None:
        """Mark thread as closed.

        Args:
            thread_ts: Slack thread timestamp
        """
        if thread_ts in self.threads:
            self.threads[thread_ts]["status"] = "closed"
            self.threads[thread_ts]["closed_at"] = datetime.utcnow()


class SlackBot:
    """Slack bot for feedback routing."""

    def __init__(self, bot_token: str, config: Optional[BotConfig] = None):
        """Initialize Slack bot.

        Args:
            bot_token: Slack bot token
            config: Bot configuration
        """
        self.bot_token = bot_token
        self.config = config or BotConfig()
        self.thread_tracker = ThreadStatusTracker()
        self.dnd_users: set = set()

    def get_bot_info(self) -> Dict[str, Any]:
        """Get bot information.

        Returns:
            Bot info dictionary
        """
        return {
            "name": self.config.name,
            "emoji": self.config.emoji,
            "greeting": self.config.greeting,
            "signature": self.config.signature
        }

    def format_message(self, content: str, include_thinking: bool = False) -> str:
        """Format bot message.

        Args:
            content: Message content
            include_thinking: Whether to show thinking process

        Returns:
            Formatted message
        """
        if include_thinking and self.config.show_thinking:
            return f"_{self.config.signature}_\n\n{content}"
        return content

    def get_thread_update_message(self, status: str, metadata: Dict[str, Any]) -> str:
        """Get thread update message.

        Args:
            status: Current status
            metadata: Status metadata

        Returns:
            Status update message
        """
        status_messages = {
            "acknowledged": "✓ Acknowledged and being reviewed",
            "assigned": f"→ Assigned to {metadata.get('assigned_to', 'team')}",
            "escalated": "⬆️ Escalated for priority attention",
            "resolved": "✓ Resolved",
            "closed": "Closed"
        }

        return status_messages.get(status, f"Status: {status}")

    def is_user_dnd(self, user_id: str) -> bool:
        """Check if user has Do Not Disturb enabled.

        Args:
            user_id: Slack user ID

        Returns:
            True if user is in DND mode
        """
        return user_id in self.dnd_users

    def set_user_dnd(self, user_id: str, enabled: bool) -> None:
        """Set user DND status.

        Args:
            user_id: Slack user ID
            enabled: DND enabled
        """
        if enabled:
            self.dnd_users.add(user_id)
        else:
            self.dnd_users.discard(user_id)

    def should_notify_user(self, user_id: str, priority: int) -> bool:
        """Determine if user should be notified.

        Args:
            user_id: Slack user ID
            priority: Notification priority (1-5, lower is higher)

        Returns:
            True if user should be notified
        """
        # Respect DND for normal priority
        if self.is_user_dnd(user_id) and priority >= 3:
            return False
        return True

    def build_acknowledgment_response(self, action: str) -> str:
        """Build acknowledgment response.

        Args:
            action: User action

        Returns:
            Response message
        """
        responses = {
            "acknowledge": "Thanks for confirming! I've noted that you've seen this.",
            "assign": "Got it, I'll add this to the team's queue.",
            "escalate": "Understood - escalating this for immediate attention.",
            "resolve": "Great! Marking this as resolved.",
        }

        return responses.get(action, "Action received.")

    def get_error_response(self, error_type: str) -> str:
        """Get error response message.

        Args:
            error_type: Type of error

        Returns:
            Error message
        """
        responses = {
            "invalid_action": "Sorry, I didn't understand that action. Try acknowledge, assign, escalate, or resolve.",
            "not_found": "Sorry, I couldn't find that feedback item.",
            "permission_denied": "Sorry, you don't have permission to perform that action.",
            "system_error": "Sorry, something went wrong. Please try again later.",
        }

        return responses.get(error_type, "An error occurred.")


class DNDAwareMessenger:
    """Sends messages respecting user DND status."""

    def __init__(self, bot: SlackBot):
        """Initialize messenger.

        Args:
            bot: Slack bot
        """
        self.bot = bot

    def send_message(self, user_id: str, message: str,
                    channel_id: Optional[str] = None,
                    priority: int = 3,
                    thread_ts: Optional[str] = None) -> bool:
        """Send message respecting DND.

        Args:
            user_id: Target user ID
            message: Message content
            channel_id: Optional channel ID
            priority: Priority level (1-5)
            thread_ts: Optional thread timestamp

        Returns:
            True if message would be sent
        """
        if not self.bot.should_notify_user(user_id, priority):
            # Queue for later delivery
            return False

        # Would call Slack API here to send message
        return True

    def send_urgent_notification(self, user_id: str, message: str,
                                 channel_id: Optional[str] = None) -> bool:
        """Send urgent notification ignoring DND.

        Args:
            user_id: Target user ID
            message: Message content
            channel_id: Optional channel ID

        Returns:
            True if message is sent
        """
        # Critical notifications bypass DND
        return True
