"""Contact identification and classification."""

from enum import Enum
from typing import Optional, Dict, Tuple
import re


class ContactTypeEnum(str, Enum):
    """Contact type classification."""
    PROSPECT = "prospect"
    CLIENT = "client"
    CHURNED = "churned"
    INTERNAL = "internal"
    UNKNOWN = "unknown"


class ContactIdentifier:
    """Identifies and classifies contacts from feedback."""

    def __init__(self, contact_db: Optional[Dict] = None):
        """Initialize contact identifier.

        Args:
            contact_db: Optional dictionary of known contacts
        """
        self.contact_db = contact_db or {}

    def identify_contact(self, text: str, email: Optional[str] = None,
                        slack_handle: Optional[str] = None,
                        account_id: Optional[str] = None) -> Tuple[ContactTypeEnum, Optional[str], Optional[str]]:
        """Identify contact from text and metadata.

        Args:
            text: Feedback text that may contain contact hints
            email: Email address if provided
            slack_handle: Slack handle if provided
            account_id: Account ID if known

        Returns:
            Tuple of (contact_type, contact_id, account_id)
        """
        # Check if email is in database
        if email:
            contact_info = self.contact_db.get(email.lower())
            if contact_info:
                return contact_info.get("type", ContactTypeEnum.UNKNOWN), email, contact_info.get("account_id")

        # Check if it's internal (mentions of team members, internal channels)
        if self._is_internal(text):
            return ContactTypeEnum.INTERNAL, None, None

        # Check if it mentions churn/leaving
        if self._indicates_churn(text):
            return ContactTypeEnum.CHURNED, None, account_id

        # If account_id is provided, likely a client
        if account_id:
            return ContactTypeEnum.CLIENT, account_id, account_id

        # Default to prospect
        return ContactTypeEnum.PROSPECT, None, account_id

    def _is_internal(self, text: str) -> bool:
        """Check if text indicates internal feedback.

        Args:
            text: Feedback text

        Returns:
            True if appears to be internal
        """
        internal_indicators = [
            r"\bteam\b", r"\bour team\b", r"\binternal\b", r"\bstaff\b",
            r"\bemployee\b", r"\bco-worker\b", r"\bcolleague\b"
        ]

        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in internal_indicators)

    def _indicates_churn(self, text: str) -> bool:
        """Check if text indicates churn/leaving.

        Args:
            text: Feedback text

        Returns:
            True if indicates churn
        """
        churn_indicators = [
            r"\bcancel\b", r"\bunsubscribe\b", r"\bdelete\b", r"\bleave\b",
            r"\bstop\b", r"\bquit\b", r"\bchurn\b", r"\bswitching to\b",
            r"\busing.*instead\b", r"\breplace\b", r"\bmigrat"
        ]

        text_lower = text.lower()
        return sum(1 for pattern in churn_indicators if re.search(pattern, text_lower)) >= 1

    def extract_email(self, text: str) -> Optional[str]:
        """Extract email address from text.

        Args:
            text: Text to search

        Returns:
            Email address if found
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None

    def extract_slack_handle(self, text: str) -> Optional[str]:
        """Extract Slack handle from text.

        Args:
            text: Text to search

        Returns:
            Slack handle if found
        """
        slack_pattern = r'@([a-z0-9._-]+)'
        match = re.search(slack_pattern, text.lower())
        return match.group(1) if match else None
