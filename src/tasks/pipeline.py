"""Feedback processing pipeline orchestrator."""

from typing import Dict, Any

from src.agents.intake import IntakeAgent
from src.agents.classifier import ClassifierAgent
from src.agents.router import RouterAgent
from src.agents.responder import ResponderAgent
from src.schemas.feedback import FeedbackItem, FeedbackRouting, FeedbackStatusEnum


class FeedbackPipeline:
    """Orchestrates the full feedback processing pipeline.

    Runs feedback through all four stages:
      1. Intake -- normalise raw input into a FeedbackItem
      2. Classify -- sentiment, category, themes, confidence
      3. Route -- team assignment, escalation, priority
      4. Respond -- generate an appropriate response
    """

    def __init__(
        self,
        intake_agent: IntakeAgent | None = None,
        classifier_agent: ClassifierAgent | None = None,
        router_agent: RouterAgent | None = None,
        responder_agent: ResponderAgent | None = None,
    ):
        """Initialise pipeline with agent instances.

        Args:
            intake_agent: Agent for normalising raw feedback.
            classifier_agent: Agent for classifying feedback.
            router_agent: Agent for routing classified feedback.
            responder_agent: Agent for generating responses.
        """
        self.intake_agent = intake_agent or IntakeAgent()
        self.classifier_agent = classifier_agent or ClassifierAgent(use_llm=False)
        self.router_agent = router_agent or RouterAgent()
        self.responder_agent = responder_agent or ResponderAgent()

    def process(self, raw_feedback: Dict[str, Any], channel: str) -> FeedbackItem:
        """Run raw feedback through the complete pipeline.

        Args:
            raw_feedback: Raw feedback dict as received from the channel.
            channel: Source channel identifier (e.g. "slack", "email",
                     "website_form").

        Returns:
            A fully-populated FeedbackItem with classification, routing,
            and response fields set.
        """
        # 1. Intake: normalise into a FeedbackItem
        feedback_item = self.intake_agent.normalize_feedback(raw_feedback, channel)

        # 2. Classify: analyse sentiment, category, themes
        classification = self.classifier_agent.classify(feedback_item)
        feedback_item.classification = classification
        feedback_item.lifecycle.status = FeedbackStatusEnum.CLASSIFIED

        # 3. Route: determine team, priority, escalation
        routing_decision = self.router_agent.route(feedback_item)
        feedback_item.routing = FeedbackRouting(
            action=routing_decision.action,
            assigned_team=routing_decision.assigned_team,
            assigned_individual=routing_decision.assigned_individual,
            channel=routing_decision.channel,
            escalated=routing_decision.escalated,
            escalation_reason=routing_decision.escalation_reason,
            recommended_action=routing_decision.recommended_action,
        )
        feedback_item.lifecycle.status = FeedbackStatusEnum.ROUTED

        # 4. Respond: generate the appropriate response
        response = self.responder_agent.generate_response(feedback_item, routing_decision)
        feedback_item.response = response
        feedback_item.lifecycle.status = FeedbackStatusEnum.RESPONDED

        return feedback_item
