"""Website webhook handlers for feedback ingestion."""

from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import hmac
from fastapi import HTTPException, Header
from src.agents.intake import IntakeAgent
from src.schemas.feedback import FeedbackItem


class WebsiteWebhookHandler:
    """Handles website feedback webhooks."""

    def __init__(self, webhook_secret: Optional[str] = None, intake_agent: Optional[IntakeAgent] = None):
        """Initialize webhook handler.

        Args:
            webhook_secret: Secret for validating webhook signature
            intake_agent: Intake agent for normalizing feedback
        """
        self.webhook_secret = webhook_secret
        self.intake_agent = intake_agent or IntakeAgent()

    def verify_signature(self, payload: str, signature: str) -> bool:
        """Verify webhook signature.

        Args:
            payload: Request payload
            signature: Signature from header

        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            return True

        expected_sig = hmac.new(
            self.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_sig, signature)

    def handle_form_submission(self, form_data: Dict[str, Any],
                             signature: Optional[str] = None) -> FeedbackItem:
        """Handle website form submission.

        Args:
            form_data: Form submission data
            signature: Optional webhook signature

        Returns:
            Normalized FeedbackItem

        Raises:
            HTTPException if signature invalid
        """
        # Validate signature if provided
        if signature:
            payload = str(sorted(form_data.items()))
            if not self.verify_signature(payload, signature):
                raise HTTPException(status_code=401, detail="Invalid signature")

        # Normalize form data
        normalized_data = {
            "form_id": form_data.get("id", f"form_{datetime.utcnow().timestamp()}"),
            "name": form_data.get("name", "Unknown"),
            "email": form_data.get("email", ""),
            "message": form_data.get("message", form_data.get("feedback", "")),
            "page_url": form_data.get("page_url", form_data.get("referrer", "")),
            "ip_address": form_data.get("ip_address", ""),
            "timestamp": form_data.get("timestamp", datetime.utcnow().isoformat()),
        }

        return self.intake_agent.normalize_website_form(normalized_data)

    def handle_chat_message(self, chat_data: Dict[str, Any],
                           signature: Optional[str] = None) -> FeedbackItem:
        """Handle website chat widget message.

        Args:
            chat_data: Chat message data
            signature: Optional webhook signature

        Returns:
            Normalized FeedbackItem

        Raises:
            HTTPException if signature invalid
        """
        # Validate signature if provided
        if signature:
            payload = str(sorted(chat_data.items()))
            if not self.verify_signature(payload, signature):
                raise HTTPException(status_code=401, detail="Invalid signature")

        # Normalize chat data
        normalized_data = {
            "form_id": chat_data.get("session_id", f"chat_{datetime.utcnow().timestamp()}"),
            "name": chat_data.get("visitor_name", "Chat Visitor"),
            "email": chat_data.get("visitor_email", ""),
            "message": chat_data.get("message", ""),
            "page_url": chat_data.get("page_url", ""),
            "ip_address": chat_data.get("visitor_ip", ""),
            "timestamp": chat_data.get("timestamp", datetime.utcnow().isoformat()),
        }

        return self.intake_agent.normalize_website_form(normalized_data)

    def handle_404_feedback(self, page_data: Dict[str, Any],
                           signature: Optional[str] = None) -> FeedbackItem:
        """Handle 404 page feedback.

        Args:
            page_data: 404 page feedback data
            signature: Optional webhook signature

        Returns:
            Normalized FeedbackItem

        Raises:
            HTTPException if signature invalid
        """
        # Validate signature if provided
        if signature:
            payload = str(sorted(page_data.items()))
            if not self.verify_signature(payload, signature):
                raise HTTPException(status_code=401, detail="Invalid signature")

        # Build feedback message for 404
        requested_page = page_data.get("requested_url", "unknown page")
        referrer = page_data.get("referrer", "direct")

        message = f"User unable to find what they were looking for at {requested_page}"

        normalized_data = {
            "form_id": page_data.get("session_id", f"404_{datetime.utcnow().timestamp()}"),
            "name": "404 Visitor",
            "email": page_data.get("email", ""),
            "message": message,
            "page_url": requested_page,
            "ip_address": page_data.get("ip_address", ""),
            "timestamp": page_data.get("timestamp", datetime.utcnow().isoformat()),
        }

        return self.intake_agent.normalize_website_form(normalized_data)


class RateLimiter:
    """Simple rate limiter for webhooks."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """Initialize rate limiter.

        Args:
            max_requests: Max requests allowed
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}

    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed.

        Args:
            identifier: Request identifier (IP, API key, etc.)

        Returns:
            True if request is allowed
        """
        now = datetime.utcnow().timestamp()
        window_start = now - self.window_seconds

        if identifier not in self.requests:
            self.requests[identifier] = []

        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]

        # Check limit
        if len(self.requests[identifier]) >= self.max_requests:
            return False

        # Add current request
        self.requests[identifier].append(now)
        return True
