"""Router agent for determining feedback routing."""

from typing import Optional

from src.schemas.feedback import FeedbackItem
from src.schemas.routing import RoutingDecision
from src.routing.engine import RoutingEngine
from src.routing.rules import RuleEngine, DEFAULT_RULES
from src.routing.escalation import EscalationEngine
from src.routing.assignment import TeamAssignmentManager


class RouterAgent:
    """Routes classified feedback to appropriate teams."""

    def __init__(self, routing_engine: Optional[RoutingEngine] = None):
        """Initialize router agent.

        Args:
            routing_engine: Optional custom routing engine
        """
        if routing_engine:
            self.routing_engine = routing_engine
        else:
            # Initialize with default components
            rule_engine = RuleEngine()
            for rule in DEFAULT_RULES:
                rule_engine.add_rule(rule)

            escalation_engine = EscalationEngine()
            team_manager = TeamAssignmentManager()

            self.routing_engine = RoutingEngine(
                rule_engine=rule_engine,
                escalation_engine=escalation_engine,
                team_manager=team_manager
            )

    def route(self, feedback_item: FeedbackItem) -> RoutingDecision:
        """Route classified feedback item.

        Args:
            feedback_item: Classified feedback item

        Returns:
            Routing decision
        """
        return self.routing_engine.route(feedback_item)
