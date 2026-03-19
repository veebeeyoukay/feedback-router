"""Routing rule definitions and management."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import yaml


class ConditionType(str, Enum):
    """Types of rule conditions."""
    EQUALS = "equals"
    IN = "in"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    NOT_EQUALS = "not_equals"


class RuleAction(str, Enum):
    """Actions that rules can trigger."""
    ROUTE_TO_SALES = "route_to_sales"
    ROUTE_TO_SUPPORT = "route_to_support"
    ROUTE_TO_PRODUCT = "route_to_product"
    ESCALATE = "escalate"
    AUTO_RESPOND = "auto_respond"
    REQUIRE_HUMAN = "require_human"


@dataclass
class Condition:
    """A single rule condition."""
    field: str
    condition_type: ConditionType
    value: Any

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate condition against context.

        Args:
            context: Dictionary of field values

        Returns:
            True if condition is met
        """
        field_value = context.get(self.field)

        if self.condition_type == ConditionType.EQUALS:
            return field_value == self.value
        elif self.condition_type == ConditionType.NOT_EQUALS:
            return field_value != self.value
        elif self.condition_type == ConditionType.IN:
            return field_value in self.value
        elif self.condition_type == ConditionType.CONTAINS:
            return self.value in str(field_value)
        elif self.condition_type == ConditionType.GREATER_THAN:
            return field_value > self.value
        elif self.condition_type == ConditionType.LESS_THAN:
            return field_value < self.value
        else:
            return False


@dataclass
class Rule:
    """Routing rule definition."""
    name: str
    description: str
    conditions: List[Condition]
    action: RuleAction
    target: Optional[str] = None
    priority: int = 3
    additive: bool = True
    confidence: float = 1.0

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate if all conditions match.

        Args:
            context: Dictionary of field values

        Returns:
            True if all conditions are met
        """
        return all(condition.evaluate(context) for condition in self.conditions)


class RuleEngine:
    """Manages and evaluates routing rules."""

    def __init__(self):
        """Initialize rule engine."""
        self.rules: List[Rule] = []

    def add_rule(self, rule: Rule) -> None:
        """Add a rule to the engine.

        Args:
            rule: Rule to add
        """
        self.rules.append(rule)

    def load_rules_from_yaml(self, yaml_path: str) -> None:
        """Load rules from YAML file.

        Args:
            yaml_path: Path to YAML file with rule definitions
        """
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)

        for rule_data in config.get('rules', []):
            conditions = [
                Condition(
                    field=c['field'],
                    condition_type=ConditionType(c['type']),
                    value=c['value']
                )
                for c in rule_data.get('conditions', [])
            ]

            rule = Rule(
                name=rule_data['name'],
                description=rule_data.get('description', ''),
                conditions=conditions,
                action=RuleAction(rule_data['action']),
                target=rule_data.get('target'),
                priority=rule_data.get('priority', 3),
                additive=rule_data.get('additive', True),
                confidence=rule_data.get('confidence', 1.0)
            )
            self.add_rule(rule)

    def evaluate_all(self, context: Dict[str, Any], max_matches: Optional[int] = None) -> List[Rule]:
        """Evaluate all rules against context.

        Args:
            context: Dictionary of field values to match against
            max_matches: Maximum number of rules to return (sorted by priority)

        Returns:
            List of matching rules sorted by priority
        """
        matching_rules = [rule for rule in self.rules if rule.evaluate(context)]

        # Sort by priority (lower number = higher priority)
        matching_rules.sort(key=lambda r: r.priority)

        if max_matches:
            matching_rules = matching_rules[:max_matches]

        return matching_rules

    def get_rule(self, name: str) -> Optional[Rule]:
        """Get rule by name.

        Args:
            name: Rule name

        Returns:
            Rule if found, None otherwise
        """
        return next((r for r in self.rules if r.name == name), None)


# Example default rules
DEFAULT_RULES = [
    Rule(
        name="high_value_prospect_escalation",
        description="Escalate high-value prospects with sentiment concerns",
        conditions=[
            Condition("contact_type", ConditionType.EQUALS, "prospect"),
            Condition("polarity", ConditionType.EQUALS, "negative"),
            Condition("intensity", ConditionType.GREATER_THAN, 0.7)
        ],
        action=RuleAction.ESCALATE,
        target="sales",
        priority=1,
        confidence=0.95
    ),
    Rule(
        name="critical_urgency_escalation",
        description="Always escalate critical urgency items",
        conditions=[
            Condition("urgency", ConditionType.EQUALS, "critical")
        ],
        action=RuleAction.ESCALATE,
        target="management",
        priority=1,
        confidence=0.99
    ),
    Rule(
        name="bug_reports_to_support",
        description="Route bug reports to support team",
        conditions=[
            Condition("category", ConditionType.EQUALS, "bug")
        ],
        action=RuleAction.ROUTE_TO_SUPPORT,
        target="support",
        priority=2,
        confidence=0.9
    ),
    Rule(
        name="feature_requests_to_product",
        description="Route feature requests to product team",
        conditions=[
            Condition("category", ConditionType.EQUALS, "feature")
        ],
        action=RuleAction.ROUTE_TO_PRODUCT,
        target="product",
        priority=2,
        confidence=0.9
    ),
    Rule(
        name="lost_customer_escalation",
        description="Escalate lost/churn feedback",
        conditions=[
            Condition("category", ConditionType.EQUALS, "lost")
        ],
        action=RuleAction.ESCALATE,
        target="sales",
        priority=1,
        confidence=0.95
    ),
]
