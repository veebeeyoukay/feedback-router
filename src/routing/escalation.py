"""Escalation logic and triggers."""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class EscalationTriggerEnum(str, Enum):
    """Types of escalation triggers."""
    SENTIMENT_INTENSITY_HIGH = "sentiment_intensity_high"
    NEGATIVE_SENTIMENT_ESCALATION = "negative_sentiment_escalation"
    CRITICAL_URGENCY = "critical_urgency"
    LOST_CUSTOMER = "lost_customer"
    SECURITY_ISSUE = "security_issue"
    EXECUTIVE_MENTION = "executive_mention"
    BUSINESS_IMPACT_HIGH = "business_impact_high"


@dataclass
class EscalationResult:
    """Result of escalation evaluation."""
    triggered: bool
    trigger_name: Optional[str] = None
    action: Optional[str] = None
    target: Optional[str] = None
    reason: str = ""


class EscalationEngine:
    """Evaluates escalation triggers for feedback."""

    SENTIMENT_INTENSITY_THRESHOLD = 0.8
    NEGATIVE_SENTIMENT_THRESHOLD = 0.7
    BUSINESS_IMPACT_KEYWORDS = [
        "executive", "board", "ceo", "revenue", "churn", "critical",
        "security", "breach", "compliance", "soc2", "hipaa"
    ]
    EXECUTIVE_KEYWORDS = ["executive", "ceo", "cfo", "board", "investor"]
    SECURITY_KEYWORDS = ["security", "breach", "vulnerability", "hack", "exploit", "attack"]

    def evaluate_escalation(self, feedback_context: dict) -> EscalationResult:
        """Evaluate if feedback should be escalated.

        Args:
            feedback_context: Dictionary with feedback classification and context

        Returns:
            EscalationResult with trigger information
        """
        # Check each trigger
        if self._check_sentiment_intensity_high(feedback_context):
            return EscalationResult(
                triggered=True,
                trigger_name=EscalationTriggerEnum.SENTIMENT_INTENSITY_HIGH.value,
                action="escalate",
                target="management",
                reason="High sentiment intensity indicates strong customer emotion"
            )

        if self._check_negative_sentiment_escalation(feedback_context):
            return EscalationResult(
                triggered=True,
                trigger_name=EscalationTriggerEnum.NEGATIVE_SENTIMENT_ESCALATION.value,
                action="escalate",
                target="customer_success",
                reason="Negative sentiment with moderate-to-high intensity warrants attention"
            )

        if self._check_critical_urgency(feedback_context):
            return EscalationResult(
                triggered=True,
                trigger_name=EscalationTriggerEnum.CRITICAL_URGENCY.value,
                action="escalate",
                target="management",
                reason="Critical urgency detected - immediate attention required"
            )

        if self._check_lost_customer(feedback_context):
            return EscalationResult(
                triggered=True,
                trigger_name=EscalationTriggerEnum.LOST_CUSTOMER.value,
                action="escalate",
                target="sales",
                reason="Lost customer or churn risk - sales intervention needed"
            )

        if self._check_security_issue(feedback_context):
            return EscalationResult(
                triggered=True,
                trigger_name=EscalationTriggerEnum.SECURITY_ISSUE.value,
                action="escalate",
                target="security",
                reason="Security issue detected - requires immediate security team review"
            )

        if self._check_executive_mention(feedback_context):
            return EscalationResult(
                triggered=True,
                trigger_name=EscalationTriggerEnum.EXECUTIVE_MENTION.value,
                action="escalate",
                target="management",
                reason="Executive mentioned - high visibility item"
            )

        if self._check_business_impact_high(feedback_context):
            return EscalationResult(
                triggered=True,
                trigger_name=EscalationTriggerEnum.BUSINESS_IMPACT_HIGH.value,
                action="escalate",
                target="management",
                reason="High business impact detected"
            )

        return EscalationResult(
            triggered=False,
            reason="No escalation triggers matched"
        )

    def _check_sentiment_intensity_high(self, context: dict) -> bool:
        """Check if sentiment intensity is very high.

        Args:
            context: Feedback context

        Returns:
            True if sentiment intensity exceeds threshold
        """
        intensity = context.get("intensity", 0)
        return intensity > self.SENTIMENT_INTENSITY_THRESHOLD

    def _check_negative_sentiment_escalation(self, context: dict) -> bool:
        """Check if negative sentiment is concerning.

        Args:
            context: Feedback context

        Returns:
            True if negative sentiment with meaningful intensity
        """
        polarity = context.get("polarity", "neutral")
        intensity = context.get("intensity", 0)
        return polarity == "negative" and intensity > self.NEGATIVE_SENTIMENT_THRESHOLD

    def _check_critical_urgency(self, context: dict) -> bool:
        """Check if urgency is critical.

        Args:
            context: Feedback context

        Returns:
            True if urgency is critical
        """
        urgency = context.get("urgency", "low")
        return urgency == "critical"

    def _check_lost_customer(self, context: dict) -> bool:
        """Check if feedback indicates lost customer.

        Args:
            context: Feedback context

        Returns:
            True if lost customer category detected
        """
        category = context.get("category", "")
        contact_type = context.get("contact_type", "")
        return category == "lost" or contact_type == "churned"

    def _check_security_issue(self, context: dict) -> bool:
        """Check if security issue mentioned.

        Args:
            context: Feedback context

        Returns:
            True if security issue detected
        """
        text = context.get("raw_text", "").lower()
        return any(keyword in text for keyword in self.SECURITY_KEYWORDS)

    def _check_executive_mention(self, context: dict) -> bool:
        """Check if executive mentioned.

        Args:
            context: Feedback context

        Returns:
            True if executive mention detected
        """
        text = context.get("raw_text", "").lower()
        return any(keyword in text for keyword in self.EXECUTIVE_KEYWORDS)

    def _check_business_impact_high(self, context: dict) -> bool:
        """Check if business impact is high.

        Args:
            context: Feedback context

        Returns:
            True if high business impact detected
        """
        business_impact = context.get("business_impact", "").lower()
        raw_text = context.get("raw_text", "").lower()

        impact_indicators = ["revenue", "contract", "renewal", "expansion", "major account"]
        text_to_check = business_impact + " " + raw_text

        return any(indicator in text_to_check for indicator in impact_indicators)
