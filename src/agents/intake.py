"""Intake agent for normalizing raw feedback."""

from typing import Optional, Dict, Any
from datetime import datetime
import uuid
from src.schemas.feedback import (
    FeedbackItem, FeedbackSource, FeedbackSourceEnum, FeedbackContact,
    ContactTypeEnum, FeedbackContent, FeedbackLifecycle, FeedbackStatusEnum
)
from src.classification.contact import ContactIdentifier


class IntakeAgent:
    """Normalizes raw feedback into unified schema."""

    def __init__(self, contact_db: Optional[Dict] = None):
        """Initialize intake agent.

        Args:
            contact_db: Optional contact database for identification
        """
        self.contact_identifier = ContactIdentifier(contact_db)

    def normalize_feedback(self, raw_input: Dict[str, Any], channel: str) -> FeedbackItem:
        """Normalize raw feedback input into unified FeedbackItem.

        Args:
            raw_input: Raw feedback data from channel
            channel: Source channel identifier

        Returns:
            Normalized FeedbackItem
        """
        # Generate unique ID
        feedback_id = self._generate_id()

        # Parse source information
        source = self._parse_source(raw_input, channel)

        # Identify contact
        contact = self._identify_contact(raw_input, source)

        # Parse content
        content = self._parse_content(raw_input)

        # Create feedback item
        feedback_item = FeedbackItem(
            id=feedback_id,
            timestamp=datetime.utcnow(),
            source=source,
            contact=contact,
            content=content,
            lifecycle=FeedbackLifecycle(status=FeedbackStatusEnum.RECEIVED)
        )

        return feedback_item

    def _generate_id(self) -> str:
        """Generate unique feedback ID.

        Returns:
            Unique ID
        """
        return f"fb_{uuid.uuid4().hex[:12]}"

    def _parse_source(self, raw_input: Dict[str, Any], channel: str) -> FeedbackSource:
        """Parse source information from raw input.

        Args:
            raw_input: Raw feedback data
            channel: Channel identifier

        Returns:
            FeedbackSource
        """
        source_enum = self._map_channel_to_enum(channel)

        return FeedbackSource(
            channel=source_enum,
            platform=raw_input.get("platform"),
            raw_id=raw_input.get("id", str(uuid.uuid4())),
            context=raw_input.get("context", {})
        )

    def _map_channel_to_enum(self, channel: str) -> FeedbackSourceEnum:
        """Map channel string to FeedbackSourceEnum.

        Args:
            channel: Channel identifier

        Returns:
            FeedbackSourceEnum
        """
        channel_map = {
            "website_form": FeedbackSourceEnum.WEBSITE_FORM,
            "website_chat": FeedbackSourceEnum.WEBSITE_CHAT,
            "website_404": FeedbackSourceEnum.WEBSITE_404,
            "slack": FeedbackSourceEnum.SLACK,
            "email": FeedbackSourceEnum.EMAIL,
            "twitter": FeedbackSourceEnum.TWITTER,
            "intercom": FeedbackSourceEnum.INTERCOM,
        }
        return channel_map.get(channel, FeedbackSourceEnum.EMAIL)

    def _identify_contact(self, raw_input: Dict[str, Any], source: FeedbackSource) -> FeedbackContact:
        """Identify contact from raw input.

        Args:
            raw_input: Raw feedback data
            source: Source information

        Returns:
            FeedbackContact
        """
        email = raw_input.get("email")
        text = raw_input.get("text", "")
        account_id = raw_input.get("account_id")

        # Extract contact identifiers
        if not email:
            email = self.contact_identifier.extract_email(text)

        slack_handle = raw_input.get("slack_handle")
        if not slack_handle:
            slack_handle = self.contact_identifier.extract_slack_handle(text)

        # Identify contact type
        contact_type, contact_id, identified_account = self.contact_identifier.identify_contact(
            text=text,
            email=email,
            slack_handle=slack_handle,
            account_id=account_id
        )

        return FeedbackContact(
            type=contact_type,
            id=contact_id or email or slack_handle,
            name=raw_input.get("name"),
            account=identified_account or account_id,
            history=raw_input.get("history", {})
        )

    def _parse_content(self, raw_input: Dict[str, Any]) -> FeedbackContent:
        """Parse feedback content from raw input.

        Args:
            raw_input: Raw feedback data

        Returns:
            FeedbackContent
        """
        text = raw_input.get("text", raw_input.get("message", ""))

        return FeedbackContent(
            raw_text=text,
            summary=raw_input.get("summary"),
            language=raw_input.get("language", "en")
        )

    def normalize_website_form(self, form_data: Dict[str, Any]) -> FeedbackItem:
        """Normalize website form submission.

        Args:
            form_data: Form submission data

        Returns:
            Normalized FeedbackItem
        """
        return self.normalize_feedback(
            raw_input={
                "id": form_data.get("form_id"),
                "platform": "website_form",
                "text": form_data.get("message"),
                "name": form_data.get("name"),
                "email": form_data.get("email"),
                "context": {
                    "page_url": form_data.get("page_url"),
                    "timestamp": form_data.get("timestamp"),
                    "ip_address": form_data.get("ip_address"),
                }
            },
            channel="website_form"
        )

    def normalize_slack_message(self, message_data: Dict[str, Any]) -> FeedbackItem:
        """Normalize Slack message.

        Args:
            message_data: Slack message data

        Returns:
            Normalized FeedbackItem
        """
        return self.normalize_feedback(
            raw_input={
                "id": message_data.get("ts"),
                "platform": "slack",
                "text": message_data.get("text"),
                "slack_handle": message_data.get("user"),
                "context": {
                    "channel": message_data.get("channel"),
                    "thread_ts": message_data.get("thread_ts"),
                    "reactions": message_data.get("reactions", []),
                }
            },
            channel="slack"
        )

    def normalize_email(self, email_data: Dict[str, Any]) -> FeedbackItem:
        """Normalize email feedback.

        Args:
            email_data: Email data

        Returns:
            Normalized FeedbackItem
        """
        return self.normalize_feedback(
            raw_input={
                "id": email_data.get("message_id"),
                "platform": "email",
                "text": email_data.get("body"),
                "name": email_data.get("from_name"),
                "email": email_data.get("from_email"),
                "context": {
                    "subject": email_data.get("subject"),
                    "timestamp": email_data.get("date"),
                }
            },
            channel="email"
        )
