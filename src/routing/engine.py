"""Routing decision engine."""

from typing import List, Dict, Optional
from src.schemas.feedback import FeedbackClassification, FeedbackItem
from src.schemas.routing import RoutingDecision
from src.routing.rules import Rule, RuleEngine, RuleAction
from src.routing.escalation import EscalationEngine, EscalationTriggerEnum
from src.routing.assignment import TeamAssignmentManager


class RoutingEngine:
    """Evaluates routing decisions for classified feedback."""

    # Confidence thresholds for response type
    HIGH_CONFIDENCE_THRESHOLD = 0.85
    MEDIUM_CONFIDENCE_THRESHOLD = 0.6
    LOW_CONFIDENCE_THRESHOLD = 0.0

    def __init__(self, rule_engine: Optional[RuleEngine] = None,
                 escalation_engine: Optional[EscalationEngine] = None,
                 team_manager: Optional[TeamAssignmentManager] = None):
        """Initialize routing engine.

        Args:
            rule_engine: Rule engine for evaluating rules
            escalation_engine: Escalation engine for checking escalations
            team_manager: Team assignment manager
        """
        self.rule_engine = rule_engine or RuleEngine()
        self.escalation_engine = escalation_engine or EscalationEngine()
        self.team_manager = team_manager or TeamAssignmentManager()

    def route(self, feedback_item: FeedbackItem) -> RoutingDecision:
        """Route classified feedback item.

        Args:
            feedback_item: Feedback item with classification

        Returns:
            RoutingDecision with routing information
        """
        if not feedback_item.classification:
            return self._create_default_routing(feedback_item)

        classification = feedback_item.classification
        contact_type = feedback_item.contact.type.value

        # Build evaluation context
        context = {
            "category": classification.category.value,
            "polarity": classification.sentiment.polarity.value,
            "intensity": classification.sentiment.intensity,
            "urgency": classification.sentiment.urgency.value,
            "contact_type": contact_type,
            "business_impact": classification.business_impact,
            "confidence": classification.confidence,
            "raw_text": feedback_item.content.raw_text,
            "themes": classification.themes,
        }

        # Evaluate rules
        matching_rules = self.rule_engine.evaluate_all(context)

        # Check for escalations
        escalation_result = self.escalation_engine.evaluate_escalation(context)

        # Determine response type based on confidence
        response_type = self._determine_response_type(classification.confidence, contact_type)

        # Get team assignment
        assigned_team = self.team_manager.get_team_for_category(classification.category.value)

        # Determine priority
        priority = self._determine_priority(classification.sentiment.urgency.value,
                                           classification.sentiment.intensity,
                                           contact_type)

        # Build routing decision
        routing_decision = RoutingDecision(
            action=matching_rules[0].action.value if matching_rules else "route_to_support",
            assigned_team=assigned_team,
            assigned_individual=None,  # Can be set by team assignment rules
            channel=self._determine_channel(contact_type, feedback_item.source.channel.value),
            escalated=escalation_result.triggered,
            escalation_reason=escalation_result.reason if escalation_result.triggered else None,
            escalation_trigger=escalation_result.trigger_name if escalation_result.triggered else None,
            recommended_action=self._get_recommended_action(
                classification.category.value,
                classification.sentiment.urgency.value,
                escalation_result.triggered
            ),
            response_type=response_type,
            priority=priority,
            rules_applied=[rule.name for rule in matching_rules]
        )

        return routing_decision

    def _create_default_routing(self, feedback_item: FeedbackItem) -> RoutingDecision:
        """Create default routing for unclassified feedback.

        Args:
            feedback_item: Feedback item

        Returns:
            Default routing decision
        """
        return RoutingDecision(
            action="route_to_support",
            assigned_team="support",
            assigned_individual=None,
            channel=self._determine_channel(feedback_item.contact.type.value,
                                           feedback_item.source.channel.value),
            escalated=False,
            escalation_reason=None,
            escalation_trigger=None,
            recommended_action="Review and classify",
            response_type="flag_human",
            priority=3,
            rules_applied=[]
        )

    def _determine_response_type(self, confidence: float, contact_type: str) -> str:
        """Determine response type based on confidence.

        Args:
            confidence: Classification confidence (0-1)
            contact_type: Type of contact

        Returns:
            Response type enum value
        """
        if confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
            return "auto_acknowledge"
        elif confidence >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            if contact_type in ["prospect", "client"]:
                return "draft_faq"
            else:
                return "draft_complex"
        else:
            return "flag_human"

    def _determine_priority(self, urgency: str, intensity: float, contact_type: str) -> int:
        """Determine priority level (1-5, lower is higher priority).

        Args:
            urgency: Urgency level
            intensity: Sentiment intensity
            contact_type: Type of contact

        Returns:
            Priority level 1-5
        """
        if urgency == "critical":
            return 1
        elif urgency == "high" and intensity > 0.7:
            return 1
        elif urgency == "high":
            return 2
        elif contact_type in ["client", "churned"]:
            return 2
        elif urgency == "medium":
            return 3
        else:
            return 4

    def _determine_channel(self, contact_type: str, source_channel: str) -> str:
        """Determine preferred response channel.

        Args:
            contact_type: Type of contact
            source_channel: Source feedback channel

        Returns:
            Preferred response channel
        """
        # Respond through same channel when possible
        if source_channel in ["slack", "email"]:
            return source_channel

        # Default responses
        if contact_type in ["client", "prospect"]:
            return "email"
        elif contact_type == "internal":
            return "slack"
        else:
            return "email"

    def _get_recommended_action(self, category: str, urgency: str, escalated: bool) -> str:
        """Get recommended next action.

        Args:
            category: Feedback category
            urgency: Urgency level
            escalated: Whether escalated

        Returns:
            Recommended action string
        """
        if escalated:
            return "Prioritize for immediate review"

        if category == "bug":
            return "Verify bug reproduction and assign to engineering"
        elif category == "feature":
            return "Add to product roadmap for evaluation"
        elif category == "complaint":
            if urgency == "critical":
                return "Schedule immediate escalation call"
            else:
                return "Review concerns and prepare response"
        elif category == "lost":
            return "Schedule sales intervention call"
        elif category == "question":
            return "Provide detailed help or escalate to support"
        else:
            return "Route to appropriate team for action"
