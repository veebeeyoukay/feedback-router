"""Responder agent for generating responses."""

from typing import Optional
from src.schemas.feedback import (
    FeedbackItem, FeedbackResponse, ResponseTypeEnum, CategoryEnum
)
from src.schemas.routing import RoutingDecision


class ResponderAgent:
    """Generates responses based on feedback type and routing."""

    # Response templates by category
    RESPONSE_TEMPLATES = {
        "auto_acknowledge": {
            "template": "Thank you for reaching out! We appreciate your feedback and will review it shortly.",
            "tone": "warm",
        },
        "faq_bug": {
            "template": "Thank you for reporting this issue. We're investigating this bug and will provide an update soon.",
            "tone": "professional",
        },
        "faq_feature": {
            "template": "Thank you for the feature suggestion! We'll pass this along to our product team for consideration.",
            "tone": "professional",
        },
        "faq_question": {
            "template": "Great question! Here's how you can [ACTION]. If you need more help, please reach out to our support team.",
            "tone": "helpful",
        },
        "faq_complaint": {
            "template": "We're sorry to hear about your experience. We'd like to make this right. Our team will be in touch shortly.",
            "tone": "empathetic",
        },
    }

    def generate_response(self, feedback_item: FeedbackItem,
                         routing_decision: RoutingDecision) -> FeedbackResponse:
        """Generate response for feedback item.

        Args:
            feedback_item: Feedback item
            routing_decision: Routing decision

        Returns:
            Generated response
        """
        response_type = self._map_response_type(routing_decision.response_type)

        if response_type == ResponseTypeEnum.AUTO_ACKNOWLEDGE:
            return self._generate_auto_acknowledge(feedback_item, routing_decision)
        elif response_type == ResponseTypeEnum.DRAFT_FAQ:
            return self._generate_draft_faq(feedback_item, routing_decision)
        elif response_type == ResponseTypeEnum.DRAFT_COMPLEX:
            return self._generate_draft_complex(feedback_item, routing_decision)
        else:  # FLAG_HUMAN
            return self._generate_flag_human(feedback_item, routing_decision)

    def _map_response_type(self, response_type: str) -> ResponseTypeEnum:
        """Map string response type to enum.

        Args:
            response_type: Response type string

        Returns:
            ResponseTypeEnum
        """
        type_map = {
            "auto_acknowledge": ResponseTypeEnum.AUTO_ACKNOWLEDGE,
            "draft_faq": ResponseTypeEnum.DRAFT_FAQ,
            "draft_complex": ResponseTypeEnum.DRAFT_COMPLEX,
            "flag_human": ResponseTypeEnum.FLAG_HUMAN,
        }
        return type_map.get(response_type, ResponseTypeEnum.FLAG_HUMAN)

    def _generate_auto_acknowledge(self, feedback_item: FeedbackItem,
                                  routing_decision: RoutingDecision) -> FeedbackResponse:
        """Generate auto-acknowledge response.

        Args:
            feedback_item: Feedback item
            routing_decision: Routing decision

        Returns:
            Auto-acknowledge response
        """
        response_text = f"""
Thank you for contacting us! We appreciate your feedback.

Your message has been received and routed to our {routing_decision.assigned_team} team.

We'll get back to you shortly.

Best regards,
The Team
        """.strip()

        return FeedbackResponse(
            auto_responded=True,
            response_text=response_text,
            response_type=ResponseTypeEnum.AUTO_ACKNOWLEDGE
        )

    def _generate_draft_faq(self, feedback_item: FeedbackItem,
                           routing_decision: RoutingDecision) -> FeedbackResponse:
        """Generate draft FAQ-style response.

        Args:
            feedback_item: Feedback item
            routing_decision: Routing decision

        Returns:
            Draft FAQ response
        """
        category = feedback_item.classification.category if feedback_item.classification else None
        category_key = category.value if category else "auto_acknowledge"

        template_key = f"faq_{category_key}"
        template = self.RESPONSE_TEMPLATES.get(template_key, self.RESPONSE_TEMPLATES["auto_acknowledge"])

        response_text = f"""
{template['template']}

[DRAFT: This response is ready for human review and customization]

Suggested Team: {routing_decision.assigned_team}
Recommended Action: {routing_decision.recommended_action}
        """.strip()

        return FeedbackResponse(
            auto_responded=False,
            response_text=response_text,
            response_type=ResponseTypeEnum.DRAFT_FAQ
        )

    def _generate_draft_complex(self, feedback_item: FeedbackItem,
                               routing_decision: RoutingDecision) -> FeedbackResponse:
        """Generate draft complex response.

        Args:
            feedback_item: Feedback item
            routing_decision: Routing decision

        Returns:
            Draft complex response
        """
        text = feedback_item.content.raw_text

        response_text = f"""
Thank you for taking the time to share your feedback with us.

We understand your concern about: {text[:100]}...

[DRAFT: Detailed response required]

Key Points to Address:
- [Address main concern]
- [Provide context or explanation]
- [Suggest next steps]

Assigned to: {routing_decision.assigned_team}
Priority: {routing_decision.priority}

[AWAITING HUMAN REVIEW AND CUSTOMIZATION]
        """.strip()

        return FeedbackResponse(
            auto_responded=False,
            response_text=response_text,
            response_type=ResponseTypeEnum.DRAFT_COMPLEX
        )

    def _generate_flag_human(self, feedback_item: FeedbackItem,
                            routing_decision: RoutingDecision) -> FeedbackResponse:
        """Flag for human review with context.

        Args:
            feedback_item: Feedback item
            routing_decision: Routing decision

        Returns:
            Flagged for human response
        """
        response_text = f"""
[FLAGGED FOR HUMAN REVIEW]

Feedback Summary: {feedback_item.content.raw_text[:150]}...

Classification Confidence: {feedback_item.classification.confidence if feedback_item.classification else 'N/A'}
Recommended Team: {routing_decision.assigned_team}
Priority: {routing_decision.priority}
Escalated: {routing_decision.escalated}

Human should compose an appropriate response based on the above context.
        """.strip()

        return FeedbackResponse(
            auto_responded=False,
            response_text=response_text,
            response_type=ResponseTypeEnum.FLAG_HUMAN
        )
