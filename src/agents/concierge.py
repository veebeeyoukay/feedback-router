"""Concierge agent for handling lost visitors."""

from dataclasses import dataclass
from typing import Optional
from src.schemas.feedback import FeedbackItem


@dataclass
class ConciergeResponse:
    """Response from concierge agent."""
    message: str
    tone: str
    should_escalate: bool
    escalation_reason: Optional[str] = None


class ConciergeAgent:
    """Handles lost visitors with warm, patient approach."""

    SYSTEM_PROMPT = """
You are a warm, patient, and empathetic concierge assistant for a SaaS company.
Your goal is to help visitors who are lost, confused, or frustrated.

Key principles:
1. Never be dismissive of their concerns
2. Show genuine understanding and empathy
3. Offer practical help and next steps
4. Be warm but professional
5. Escalate when appropriate (frustrated, angry, or executive)

Tone guidelines:
- Use conversational, friendly language
- Avoid corporate jargon
- Acknowledge their feelings
- Provide specific, actionable suggestions
"""

    def __init__(self):
        """Initialize concierge agent."""
        self.system_prompt = self.SYSTEM_PROMPT

    def handle_lost_visitor(self, feedback_item: FeedbackItem) -> ConciergeResponse:
        """Handle feedback from potentially lost visitor.

        Args:
            feedback_item: Feedback from visitor

        Returns:
            Concierge response
        """
        text = feedback_item.content.raw_text.lower()
        contact_name = feedback_item.contact.name or "there"

        # Detect frustration level
        frustration_level = self._detect_frustration(text)

        # Generate appropriate response
        if frustration_level == "high":
            return self._handle_frustrated_visitor(feedback_item, contact_name)
        elif frustration_level == "medium":
            return self._handle_confused_visitor(feedback_item, contact_name)
        else:
            return self._handle_curious_visitor(feedback_item, contact_name)

    def _detect_frustration(self, text: str) -> str:
        """Detect visitor frustration level.

        Args:
            text: Feedback text

        Returns:
            'high', 'medium', or 'low'
        """
        high_frustration = [
            "hate", "terrible", "worst", "useless", "never", "impossible",
            "angry", "frustrated", "annoyed", "disappointed", "ridiculous"
        ]

        medium_frustration = [
            "confused", "lost", "hard", "difficult", "can't find",
            "unclear", "help", "question", "not sure", "unsure"
        ]

        high_count = sum(1 for word in high_frustration if word in text)
        medium_count = sum(1 for word in medium_frustration if word in text)

        if high_count >= 2:
            return "high"
        elif medium_count >= 2 or high_count >= 1:
            return "medium"
        else:
            return "low"

    def _handle_frustrated_visitor(self, feedback_item: FeedbackItem,
                                   contact_name: str) -> ConciergeResponse:
        """Handle frustrated visitor.

        Args:
            feedback_item: Feedback item
            contact_name: Visitor name

        Returns:
            ConciergeResponse
        """
        message = f"""
Hi {contact_name},

I'm sorry you've had a frustrating experience. We genuinely want to help and make this right.

Let me connect you directly with someone on our team who can give your concern the attention it deserves.
They'll reach out within the next 2 hours to understand exactly what's going on and work toward a solution.

Is there anything specific we should know about your situation before we connect?

Thanks for giving us the chance to help.
        """.strip()

        return ConciergeResponse(
            message=message,
            tone="empathetic_and_warm",
            should_escalate=True,
            escalation_reason="Frustrated visitor - requires immediate human attention"
        )

    def _handle_confused_visitor(self, feedback_item: FeedbackItem,
                                contact_name: str) -> ConciergeResponse:
        """Handle confused visitor.

        Args:
            feedback_item: Feedback item
            contact_name: Visitor name

        Returns:
            ConciergeResponse
        """
        text = feedback_item.content.raw_text

        # Try to identify what they're looking for
        guidance = self._suggest_next_steps(text)

        message = f"""
Hi {contact_name},

Thanks for reaching out! I can tell you're trying to figure something out, and I'm here to help.

Based on what you mentioned, here are some resources that might help:
{guidance}

If you're still stuck after checking those out, I'd love to connect you with someone from our team who can walk you through it step-by-step.

What would be most helpful for you right now?
        """.strip()

        return ConciergeResponse(
            message=message,
            tone="helpful_and_friendly",
            should_escalate=False
        )

    def _handle_curious_visitor(self, feedback_item: FeedbackItem,
                               contact_name: str) -> ConciergeResponse:
        """Handle curious visitor.

        Args:
            feedback_item: Feedback item
            contact_name: Visitor name

        Returns:
            ConciergeResponse
        """
        message = f"""
Hi {contact_name},

Thanks for reaching out and for your interest! I love your curiosity.

Here are some great ways to explore further:
- Check out our documentation at docs.example.com
- Watch our quick-start video at youtube.com/example
- Schedule a demo with our team at example.com/demo

Feel free to reach out if you have any other questions. We're here to help!
        """.strip()

        return ConciergeResponse(
            message=message,
            tone="warm_and_encouraging",
            should_escalate=False
        )

    def _suggest_next_steps(self, text: str) -> str:
        """Suggest next steps based on visitor text.

        Args:
            text: Visitor feedback

        Returns:
            Suggested next steps
        """
        suggestions = []

        text_lower = text.lower()

        # Feature questions
        if any(word in text_lower for word in ["feature", "how do", "can i", "is it possible"]):
            suggestions.append("- Feature guide: www.example.com/features")
            suggestions.append("- Capabilities overview: www.example.com/docs/capabilities")

        # Pricing
        if any(word in text_lower for word in ["price", "cost", "plan", "payment"]):
            suggestions.append("- Pricing details: www.example.com/pricing")
            suggestions.append("- Compare plans: www.example.com/pricing/compare")

        # Setup/integration
        if any(word in text_lower for word in ["setup", "install", "integrate", "connect"]):
            suggestions.append("- Getting started guide: www.example.com/docs/getting-started")
            suggestions.append("- Integration docs: www.example.com/docs/integrations")

        # General help
        if not suggestions:
            suggestions.append("- Documentation: www.example.com/docs")
            suggestions.append("- Knowledge base: www.example.com/kb")
            suggestions.append("- FAQ: www.example.com/faq")

        return "\n".join(suggestions)
