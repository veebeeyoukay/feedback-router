"""Unit tests for channel handlers: WebsiteWebhookHandler, RateLimiter, SlackEventHandler."""

import pytest
import hashlib
import hmac
import time

from src.channels.website.webhook import WebsiteWebhookHandler, RateLimiter
from src.channels.slack.events import SlackEventHandler
from src.schemas.feedback import FeedbackItem, FeedbackSourceEnum


# ===========================================================================
# WebsiteWebhookHandler tests
# ===========================================================================

class TestWebsiteWebhookHandlerFormSubmission:
    """Test WebsiteWebhookHandler.handle_form_submission()."""

    def test_handle_form_submission_basic(self):
        handler = WebsiteWebhookHandler()
        form_data = {
            "id": "form_001",
            "name": "Jane Doe",
            "email": "jane@example.com",
            "message": "I need help with pricing.",
            "page_url": "https://example.com/pricing",
        }
        item = handler.handle_form_submission(form_data)
        assert isinstance(item, FeedbackItem)
        assert item.source.channel == FeedbackSourceEnum.WEBSITE_FORM
        assert item.content.raw_text == "I need help with pricing."
        assert item.contact.name == "Jane Doe"

    def test_handle_form_submission_with_feedback_field(self):
        handler = WebsiteWebhookHandler()
        form_data = {
            "feedback": "Great product!",
            "name": "Test User",
        }
        item = handler.handle_form_submission(form_data)
        assert item.content.raw_text == "Great product!"

    def test_handle_form_submission_minimal_data(self):
        handler = WebsiteWebhookHandler()
        form_data = {"message": "Just a message."}
        item = handler.handle_form_submission(form_data)
        assert isinstance(item, FeedbackItem)
        assert item.content.raw_text == "Just a message."

    def test_handle_form_submission_defaults_name_to_unknown(self):
        handler = WebsiteWebhookHandler()
        form_data = {"message": "Anonymous feedback"}
        item = handler.handle_form_submission(form_data)
        assert item.contact.name == "Unknown"


class TestWebsiteWebhookHandlerChatMessage:
    """Test WebsiteWebhookHandler.handle_chat_message()."""

    def test_handle_chat_message(self):
        handler = WebsiteWebhookHandler()
        chat_data = {
            "session_id": "chat_001",
            "visitor_name": "Chat User",
            "visitor_email": "chatuser@example.com",
            "message": "I'm looking for your API documentation.",
            "page_url": "https://example.com/docs",
            "visitor_ip": "10.0.0.1",
        }
        item = handler.handle_chat_message(chat_data)
        assert isinstance(item, FeedbackItem)
        assert item.source.channel == FeedbackSourceEnum.WEBSITE_FORM
        assert item.content.raw_text == "I'm looking for your API documentation."
        assert item.contact.name == "Chat User"

    def test_handle_chat_message_defaults_visitor_name(self):
        handler = WebsiteWebhookHandler()
        chat_data = {"message": "Hello!"}
        item = handler.handle_chat_message(chat_data)
        assert item.contact.name == "Chat Visitor"


class TestWebsiteWebhookHandler404Feedback:
    """Test WebsiteWebhookHandler.handle_404_feedback()."""

    def test_handle_404_feedback(self):
        handler = WebsiteWebhookHandler()
        page_data = {
            "requested_url": "/old/page/that/moved",
            "referrer": "https://google.com",
            "session_id": "sess_404_001",
        }
        item = handler.handle_404_feedback(page_data)
        assert isinstance(item, FeedbackItem)
        assert "/old/page/that/moved" in item.content.raw_text
        assert item.contact.name == "404 Visitor"

    def test_handle_404_feedback_unknown_page(self):
        handler = WebsiteWebhookHandler()
        page_data = {}
        item = handler.handle_404_feedback(page_data)
        assert "unknown page" in item.content.raw_text


class TestWebsiteWebhookHandlerVerifySignature:
    """Test WebsiteWebhookHandler.verify_signature()."""

    def test_verify_signature_valid(self):
        secret = "my_webhook_secret"
        handler = WebsiteWebhookHandler(webhook_secret=secret)

        payload = "some payload data"
        expected_sig = hmac.new(
            secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()

        assert handler.verify_signature(payload, expected_sig) is True

    def test_verify_signature_invalid(self):
        secret = "my_webhook_secret"
        handler = WebsiteWebhookHandler(webhook_secret=secret)

        assert handler.verify_signature("some payload", "invalid_signature") is False

    def test_verify_signature_no_secret_always_true(self):
        handler = WebsiteWebhookHandler(webhook_secret=None)
        assert handler.verify_signature("any payload", "any signature") is True

    def test_form_submission_with_invalid_signature_raises(self):
        secret = "test_secret"
        handler = WebsiteWebhookHandler(webhook_secret=secret)
        form_data = {"message": "test"}

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            handler.handle_form_submission(form_data, signature="bad_sig")
        assert exc_info.value.status_code == 401


# ===========================================================================
# RateLimiter tests
# ===========================================================================

class TestRateLimiter:
    """Test RateLimiter.is_allowed()."""

    def test_under_limit_allowed(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            assert limiter.is_allowed("user_1") is True

    def test_over_limit_denied(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            limiter.is_allowed("user_1")
        assert limiter.is_allowed("user_1") is False

    def test_different_identifiers_independent(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        limiter.is_allowed("user_1")
        limiter.is_allowed("user_1")
        assert limiter.is_allowed("user_1") is False
        assert limiter.is_allowed("user_2") is True

    def test_first_request_always_allowed(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        assert limiter.is_allowed("new_user") is True

    def test_rate_limiter_window_resets(self):
        # Use a very short window to test reset
        limiter = RateLimiter(max_requests=1, window_seconds=0)
        assert limiter.is_allowed("user_1") is True
        # With window_seconds=0, all old requests should be cleaned immediately
        assert limiter.is_allowed("user_1") is True

    def test_rate_limiter_default_values(self):
        limiter = RateLimiter()
        assert limiter.max_requests == 100
        assert limiter.window_seconds == 60


# ===========================================================================
# SlackEventHandler tests
# ===========================================================================

class TestSlackEventHandlerMessageEvent:
    """Test SlackEventHandler.handle_message_event()."""

    def test_handle_message_from_monitored_channel(self):
        handler = SlackEventHandler()
        event_data = {
            "channel": "feedback",
            "channel_name": "feedback",
            "ts": "12345.67890",
            "text": "The dashboard is slow today.",
            "user": "U123ABC",
        }
        item = handler.handle_message_event(event_data)
        assert isinstance(item, FeedbackItem)
        assert item.source.channel == FeedbackSourceEnum.SLACK
        assert item.content.raw_text == "The dashboard is slow today."

    def test_handle_message_from_unmonitored_channel_returns_none(self):
        handler = SlackEventHandler()
        event_data = {
            "channel": "random",
            "channel_name": "random",
            "ts": "12345.67890",
            "text": "Just chatting.",
            "user": "U123ABC",
        }
        result = handler.handle_message_event(event_data)
        assert result is None

    def test_ignore_bot_messages(self):
        handler = SlackEventHandler()
        event_data = {
            "channel": "feedback",
            "channel_name": "feedback",
            "ts": "12345.67890",
            "text": "Bot announcement.",
            "user": "U123ABC",
            "bot_id": "B456DEF",
        }
        result = handler.handle_message_event(event_data)
        assert result is None

    def test_ignore_message_edits(self):
        handler = SlackEventHandler()
        event_data = {
            "channel": "feedback",
            "channel_name": "feedback",
            "ts": "12345.67890",
            "text": "Edited message.",
            "user": "U123ABC",
            "subtype": "message_changed",
        }
        result = handler.handle_message_event(event_data)
        assert result is None

    def test_handle_message_from_bugs_channel(self):
        handler = SlackEventHandler()
        event_data = {
            "channel": "bugs",
            "channel_name": "bugs",
            "ts": "99999.11111",
            "text": "Found a bug in the export feature.",
            "user": "UBUG",
        }
        item = handler.handle_message_event(event_data)
        assert isinstance(item, FeedbackItem)

    def test_handle_message_with_custom_monitored_channels(self):
        handler = SlackEventHandler(monitored_channels=["custom-channel"])
        event_data = {
            "channel": "custom-channel",
            "ts": "11111.22222",
            "text": "Custom channel feedback.",
            "user": "UCUSTOM",
        }
        item = handler.handle_message_event(event_data)
        assert isinstance(item, FeedbackItem)


class TestSlackEventHandlerShouldProcessEvent:
    """Test SlackEventHandler.should_process_event()."""

    def test_should_process_feedback_channel(self):
        handler = SlackEventHandler()
        assert handler.should_process_event("feedback") is True

    def test_should_process_bugs_channel(self):
        handler = SlackEventHandler()
        assert handler.should_process_event("bugs") is True

    def test_should_process_support_channel(self):
        handler = SlackEventHandler()
        assert handler.should_process_event("support") is True

    def test_should_not_process_random_channel(self):
        handler = SlackEventHandler()
        assert not handler.should_process_event("random")

    def test_should_process_by_channel_name(self):
        handler = SlackEventHandler()
        assert handler.should_process_event("C12345", channel_name="feedback") is True

    def test_should_not_process_unknown_id_and_name(self):
        handler = SlackEventHandler()
        assert not handler.should_process_event("C99999", channel_name="general")

    def test_custom_monitored_channels(self):
        handler = SlackEventHandler(monitored_channels=["my-channel", "my-other"])
        assert handler.should_process_event("my-channel") is True
        assert not handler.should_process_event("feedback")


class TestSlackEventHandlerAppMention:
    """Test SlackEventHandler.handle_app_mention()."""

    def test_app_mention_creates_feedback(self):
        handler = SlackEventHandler()
        event_data = {
            "ts": "12345.67890",
            "text": "<@U1234> Can you help with export issues?",
            "user": "UMENTIONED",
            "channel": "feedback",
            "thread_ts": None,
            "reactions": [],
        }
        item = handler.handle_app_mention(event_data)
        assert isinstance(item, FeedbackItem)


class TestSlackEventHandlerReactionAdded:
    """Test SlackEventHandler.handle_reaction_added()."""

    def test_negative_reaction_creates_feedback(self):
        handler = SlackEventHandler()
        event_data = {
            "reaction": "thumbsdown",
            "user": "UREACTOR",
            "item": {"ts": "12345.67890", "channel": "feedback"},
        }
        item = handler.handle_reaction_added(event_data)
        assert isinstance(item, FeedbackItem)
        assert "thumbsdown" in item.content.raw_text.lower()

    def test_positive_reaction_creates_feedback(self):
        handler = SlackEventHandler()
        event_data = {
            "reaction": "thumbsup",
            "user": "UREACTOR",
            "item": {"ts": "12345.67890", "channel": "feedback"},
        }
        item = handler.handle_reaction_added(event_data)
        assert isinstance(item, FeedbackItem)

    def test_irrelevant_reaction_returns_none(self):
        handler = SlackEventHandler()
        event_data = {
            "reaction": "eyes",
            "user": "UREACTOR",
            "item": {"ts": "12345.67890", "channel": "feedback"},
        }
        result = handler.handle_reaction_added(event_data)
        assert result is None


class TestSlackEventHandlerChannelConfig:
    """Test SlackEventHandler.get_channel_config()."""

    def test_get_channel_config_returns_all_channels(self):
        handler = SlackEventHandler()
        config = handler.get_channel_config()
        assert "feedback" in config
        assert "bugs" in config
        assert "support" in config

    def test_channel_config_has_required_fields(self):
        handler = SlackEventHandler()
        config = handler.get_channel_config()
        for channel_name, channel_cfg in config.items():
            assert "description" in channel_cfg
            assert "priority" in channel_cfg
            assert "auto_process" in channel_cfg
