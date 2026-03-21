"""Unit tests for routing engine, escalation, rules, and team assignment."""

import pytest

from src.schemas.feedback import (
    FeedbackItem,
    FeedbackSource,
    FeedbackSourceEnum,
    FeedbackContact,
    ContactTypeEnum,
    FeedbackContent,
    FeedbackClassification,
    FeedbackLifecycle,
    FeedbackStatusEnum,
    SentimentScore,
    PolarityEnum,
    UrgencyEnum,
    CategoryEnum,
    ResponseTypeEnum,
)
from src.schemas.routing import RoutingDecision
from src.routing.engine import RoutingEngine
from src.routing.escalation import EscalationEngine, EscalationTriggerEnum, EscalationResult
from src.routing.rules import (
    RuleEngine,
    Rule,
    Condition,
    ConditionType,
    RuleAction,
    DEFAULT_RULES,
)
from src.routing.assignment import TeamAssignmentManager


# ---------------------------------------------------------------------------
# Helpers to build FeedbackItem objects quickly
# ---------------------------------------------------------------------------

def _make_feedback_item(
    category=CategoryEnum.QUESTION,
    polarity=PolarityEnum.NEUTRAL,
    intensity=0.5,
    urgency=UrgencyEnum.LOW,
    contact_type=ContactTypeEnum.PROSPECT,
    business_impact="Standard review required",
    confidence=0.7,
    themes=None,
    raw_text="Some feedback text",
    source_channel=FeedbackSourceEnum.WEBSITE_FORM,
    with_classification=True,
):
    """Create a FeedbackItem for testing routing."""
    item = FeedbackItem(
        id="fb_test_routing",
        source=FeedbackSource(channel=source_channel, raw_id="test_001"),
        contact=FeedbackContact(type=contact_type),
        content=FeedbackContent(raw_text=raw_text),
        lifecycle=FeedbackLifecycle(status=FeedbackStatusEnum.CLASSIFIED),
    )
    if with_classification:
        item.classification = FeedbackClassification(
            category=category,
            sentiment=SentimentScore(polarity=polarity, intensity=intensity, urgency=urgency),
            business_impact=business_impact,
            confidence=confidence,
            themes=themes or [],
        )
    return item


# ===========================================================================
# RoutingEngine tests
# ===========================================================================

class TestRoutingEngineRoute:
    """Test RoutingEngine.route() with classified feedback."""

    def test_route_returns_routing_decision(self):
        engine = RoutingEngine()
        item = _make_feedback_item(category=CategoryEnum.BUG)
        decision = engine.route(item)
        assert isinstance(decision, RoutingDecision)

    def test_route_assigns_team(self):
        engine = RoutingEngine()
        item = _make_feedback_item(category=CategoryEnum.BUG)
        decision = engine.route(item)
        assert decision.assigned_team == "support"

    def test_route_feature_to_product(self):
        engine = RoutingEngine()
        item = _make_feedback_item(category=CategoryEnum.FEATURE)
        decision = engine.route(item)
        assert decision.assigned_team == "product"

    def test_route_complaint_to_customer_success(self):
        engine = RoutingEngine()
        item = _make_feedback_item(category=CategoryEnum.COMPLAINT)
        decision = engine.route(item)
        assert decision.assigned_team == "customer_success"

    def test_route_lost_to_sales(self):
        engine = RoutingEngine()
        item = _make_feedback_item(category=CategoryEnum.LOST)
        decision = engine.route(item)
        assert decision.assigned_team == "sales"

    def test_route_escalation_to_management(self):
        engine = RoutingEngine()
        item = _make_feedback_item(category=CategoryEnum.ESCALATION)
        decision = engine.route(item)
        assert decision.assigned_team == "management"

    def test_route_includes_recommended_action(self):
        engine = RoutingEngine()
        item = _make_feedback_item(category=CategoryEnum.BUG)
        decision = engine.route(item)
        assert len(decision.recommended_action) > 0

    def test_route_includes_channel(self):
        engine = RoutingEngine()
        item = _make_feedback_item(source_channel=FeedbackSourceEnum.SLACK)
        decision = engine.route(item)
        assert decision.channel == "slack"

    def test_route_email_source_preserves_channel(self):
        engine = RoutingEngine()
        item = _make_feedback_item(source_channel=FeedbackSourceEnum.EMAIL)
        decision = engine.route(item)
        assert decision.channel == "email"


class TestRoutingEngineDefaultRouting:
    """Test RoutingEngine._create_default_routing() for unclassified feedback."""

    def test_default_routing_for_unclassified(self):
        engine = RoutingEngine()
        item = _make_feedback_item(with_classification=False)
        decision = engine.route(item)
        assert decision.assigned_team == "support"
        assert decision.action == "route_to_support"
        assert decision.escalated is False
        assert decision.response_type == "flag_human"
        assert decision.priority == 3
        assert decision.rules_applied == []

    def test_default_routing_recommended_action(self):
        engine = RoutingEngine()
        item = _make_feedback_item(with_classification=False)
        decision = engine.route(item)
        assert decision.recommended_action == "Review and classify"


class TestRoutingEngineDetermineResponseType:
    """Test RoutingEngine._determine_response_type() at different confidence levels."""

    def test_high_confidence_auto_acknowledge(self):
        engine = RoutingEngine()
        result = engine._determine_response_type(0.90, "prospect")
        assert result == "auto_acknowledge"

    def test_exactly_high_threshold_auto_acknowledge(self):
        engine = RoutingEngine()
        result = engine._determine_response_type(0.85, "prospect")
        assert result == "auto_acknowledge"

    def test_medium_confidence_prospect_draft_faq(self):
        engine = RoutingEngine()
        result = engine._determine_response_type(0.70, "prospect")
        assert result == "draft_faq"

    def test_medium_confidence_client_draft_faq(self):
        engine = RoutingEngine()
        result = engine._determine_response_type(0.70, "client")
        assert result == "draft_faq"

    def test_medium_confidence_unknown_draft_complex(self):
        engine = RoutingEngine()
        result = engine._determine_response_type(0.70, "unknown")
        assert result == "draft_complex"

    def test_low_confidence_flag_human(self):
        engine = RoutingEngine()
        result = engine._determine_response_type(0.3, "prospect")
        assert result == "flag_human"

    def test_zero_confidence_flag_human(self):
        engine = RoutingEngine()
        result = engine._determine_response_type(0.0, "prospect")
        assert result == "flag_human"


class TestRoutingEngineDeterminePriority:
    """Test RoutingEngine._determine_priority() with various urgency/contact combos."""

    def test_critical_urgency_priority_one(self):
        engine = RoutingEngine()
        result = engine._determine_priority("critical", 0.5, "prospect")
        assert result == 1

    def test_high_urgency_high_intensity_priority_one(self):
        engine = RoutingEngine()
        result = engine._determine_priority("high", 0.8, "prospect")
        assert result == 1

    def test_high_urgency_low_intensity_priority_two(self):
        engine = RoutingEngine()
        result = engine._determine_priority("high", 0.5, "prospect")
        assert result == 2

    def test_client_contact_type_priority_two(self):
        engine = RoutingEngine()
        result = engine._determine_priority("medium", 0.5, "client")
        assert result == 2

    def test_churned_contact_type_priority_two(self):
        engine = RoutingEngine()
        result = engine._determine_priority("medium", 0.5, "churned")
        assert result == 2

    def test_medium_urgency_priority_three(self):
        engine = RoutingEngine()
        result = engine._determine_priority("medium", 0.5, "prospect")
        assert result == 3

    def test_low_urgency_priority_four(self):
        engine = RoutingEngine()
        result = engine._determine_priority("low", 0.3, "unknown")
        assert result == 4


# ===========================================================================
# EscalationEngine tests
# ===========================================================================

class TestEscalationEngine:
    """Test EscalationEngine.evaluate_escalation() for each of the 7 triggers."""

    def test_sentiment_intensity_high_trigger(self):
        engine = EscalationEngine()
        context = {
            "intensity": 0.9,
            "polarity": "neutral",
            "urgency": "low",
            "category": "question",
            "contact_type": "prospect",
            "business_impact": "Standard",
            "raw_text": "Just a question",
        }
        result = engine.evaluate_escalation(context)
        assert result.triggered is True
        assert result.trigger_name == EscalationTriggerEnum.SENTIMENT_INTENSITY_HIGH.value

    def test_negative_sentiment_escalation_trigger(self):
        engine = EscalationEngine()
        context = {
            "intensity": 0.75,
            "polarity": "negative",
            "urgency": "medium",
            "category": "complaint",
            "contact_type": "client",
            "business_impact": "Client satisfaction at risk",
            "raw_text": "Very disappointed with the service",
        }
        result = engine.evaluate_escalation(context)
        assert result.triggered is True
        # Could be sentiment_intensity_high or negative_sentiment_escalation
        assert result.trigger_name in [
            EscalationTriggerEnum.SENTIMENT_INTENSITY_HIGH.value,
            EscalationTriggerEnum.NEGATIVE_SENTIMENT_ESCALATION.value,
        ]

    def test_critical_urgency_trigger(self):
        engine = EscalationEngine()
        context = {
            "intensity": 0.5,
            "polarity": "neutral",
            "urgency": "critical",
            "category": "bug",
            "contact_type": "client",
            "business_impact": "Immediate action required",
            "raw_text": "System is down for our entire team",
        }
        result = engine.evaluate_escalation(context)
        assert result.triggered is True
        # Intensity might trip first at 0.5, but urgency=critical should trigger
        # The check order in code has intensity first, so with 0.5 intensity it should
        # not trip intensity but will trip critical_urgency
        assert result.trigger_name == EscalationTriggerEnum.CRITICAL_URGENCY.value

    def test_lost_customer_trigger(self):
        engine = EscalationEngine()
        context = {
            "intensity": 0.5,
            "polarity": "neutral",
            "urgency": "low",
            "category": "lost",
            "contact_type": "client",
            "business_impact": "Potential churn",
            "raw_text": "Thinking about alternatives",
        }
        result = engine.evaluate_escalation(context)
        assert result.triggered is True
        assert result.trigger_name == EscalationTriggerEnum.LOST_CUSTOMER.value

    def test_churned_contact_type_trigger(self):
        engine = EscalationEngine()
        context = {
            "intensity": 0.5,
            "polarity": "neutral",
            "urgency": "low",
            "category": "question",
            "contact_type": "churned",
            "business_impact": "Standard",
            "raw_text": "Some feedback",
        }
        result = engine.evaluate_escalation(context)
        assert result.triggered is True
        assert result.trigger_name == EscalationTriggerEnum.LOST_CUSTOMER.value

    def test_security_issue_trigger(self):
        engine = EscalationEngine()
        context = {
            "intensity": 0.5,
            "polarity": "neutral",
            "urgency": "low",
            "category": "question",
            "contact_type": "prospect",
            "business_impact": "Standard",
            "raw_text": "We found a vulnerability in the API endpoint",
        }
        result = engine.evaluate_escalation(context)
        assert result.triggered is True
        assert result.trigger_name == EscalationTriggerEnum.SECURITY_ISSUE.value

    def test_executive_mention_trigger(self):
        engine = EscalationEngine()
        context = {
            "intensity": 0.5,
            "polarity": "neutral",
            "urgency": "low",
            "category": "question",
            "contact_type": "prospect",
            "business_impact": "Standard",
            "raw_text": "Our CEO wants to discuss this with your leadership.",
        }
        result = engine.evaluate_escalation(context)
        assert result.triggered is True
        assert result.trigger_name == EscalationTriggerEnum.EXECUTIVE_MENTION.value

    def test_business_impact_high_trigger(self):
        engine = EscalationEngine()
        context = {
            "intensity": 0.5,
            "polarity": "neutral",
            "urgency": "low",
            "category": "question",
            "contact_type": "prospect",
            "business_impact": "Major account at risk",
            "raw_text": "Our contract renewal is coming up and we have concerns",
        }
        result = engine.evaluate_escalation(context)
        assert result.triggered is True
        assert result.trigger_name == EscalationTriggerEnum.BUSINESS_IMPACT_HIGH.value

    def test_no_escalation_for_low_risk(self):
        engine = EscalationEngine()
        context = {
            "intensity": 0.3,
            "polarity": "positive",
            "urgency": "low",
            "category": "praise",
            "contact_type": "prospect",
            "business_impact": "Standard review required",
            "raw_text": "Great product so far, looking forward to more.",
        }
        result = engine.evaluate_escalation(context)
        assert result.triggered is False
        assert result.trigger_name is None

    def test_escalation_result_has_reason(self):
        engine = EscalationEngine()
        context = {
            "intensity": 0.95,
            "polarity": "negative",
            "urgency": "high",
            "category": "complaint",
            "contact_type": "client",
            "business_impact": "Client at risk",
            "raw_text": "Very angry about the service",
        }
        result = engine.evaluate_escalation(context)
        assert result.triggered is True
        assert len(result.reason) > 0


# ===========================================================================
# RuleEngine tests
# ===========================================================================

class TestRuleEngine:
    """Test RuleEngine.evaluate_all() and related functionality."""

    def test_evaluate_all_with_matching_rule(self):
        engine = RuleEngine()
        rule = Rule(
            name="test_rule",
            description="Match bug category",
            conditions=[Condition("category", ConditionType.EQUALS, "bug")],
            action=RuleAction.ROUTE_TO_SUPPORT,
            priority=2,
        )
        engine.add_rule(rule)

        matching = engine.evaluate_all({"category": "bug"})
        assert len(matching) == 1
        assert matching[0].name == "test_rule"

    def test_evaluate_all_with_no_matching_rules(self):
        engine = RuleEngine()
        rule = Rule(
            name="bug_rule",
            description="Match bug",
            conditions=[Condition("category", ConditionType.EQUALS, "bug")],
            action=RuleAction.ROUTE_TO_SUPPORT,
        )
        engine.add_rule(rule)

        matching = engine.evaluate_all({"category": "feature"})
        assert len(matching) == 0

    def test_evaluate_all_multiple_rules_sorted_by_priority(self):
        engine = RuleEngine()
        low_priority = Rule(
            name="low_priority",
            description="Low",
            conditions=[Condition("category", ConditionType.EQUALS, "bug")],
            action=RuleAction.ROUTE_TO_SUPPORT,
            priority=5,
        )
        high_priority = Rule(
            name="high_priority",
            description="High",
            conditions=[Condition("category", ConditionType.EQUALS, "bug")],
            action=RuleAction.ESCALATE,
            priority=1,
        )
        engine.add_rule(low_priority)
        engine.add_rule(high_priority)

        matching = engine.evaluate_all({"category": "bug"})
        assert len(matching) == 2
        assert matching[0].name == "high_priority"
        assert matching[1].name == "low_priority"

    def test_evaluate_all_max_matches(self):
        engine = RuleEngine()
        for i in range(5):
            engine.add_rule(Rule(
                name=f"rule_{i}",
                description=f"Rule {i}",
                conditions=[Condition("category", ConditionType.EQUALS, "bug")],
                action=RuleAction.ROUTE_TO_SUPPORT,
                priority=i,
            ))

        matching = engine.evaluate_all({"category": "bug"}, max_matches=2)
        assert len(matching) == 2

    def test_evaluate_multi_condition_rule(self):
        engine = RuleEngine()
        rule = Rule(
            name="prospect_negative",
            description="Prospect with negative sentiment",
            conditions=[
                Condition("contact_type", ConditionType.EQUALS, "prospect"),
                Condition("polarity", ConditionType.EQUALS, "negative"),
                Condition("intensity", ConditionType.GREATER_THAN, 0.7),
            ],
            action=RuleAction.ESCALATE,
            priority=1,
        )
        engine.add_rule(rule)

        # All conditions match
        matching = engine.evaluate_all({
            "contact_type": "prospect",
            "polarity": "negative",
            "intensity": 0.8,
        })
        assert len(matching) == 1

        # One condition fails
        matching = engine.evaluate_all({
            "contact_type": "prospect",
            "polarity": "positive",
            "intensity": 0.8,
        })
        assert len(matching) == 0

    def test_get_rule_by_name(self):
        engine = RuleEngine()
        rule = Rule(
            name="my_rule",
            description="My rule",
            conditions=[],
            action=RuleAction.AUTO_RESPOND,
        )
        engine.add_rule(rule)

        found = engine.get_rule("my_rule")
        assert found is not None
        assert found.name == "my_rule"

    def test_get_rule_nonexistent_returns_none(self):
        engine = RuleEngine()
        found = engine.get_rule("nonexistent")
        assert found is None


class TestConditionEvaluation:
    """Test individual Condition evaluation."""

    def test_equals_condition(self):
        cond = Condition("field", ConditionType.EQUALS, "value")
        assert cond.evaluate({"field": "value"}) is True
        assert cond.evaluate({"field": "other"}) is False

    def test_not_equals_condition(self):
        cond = Condition("field", ConditionType.NOT_EQUALS, "value")
        assert cond.evaluate({"field": "other"}) is True
        assert cond.evaluate({"field": "value"}) is False

    def test_in_condition(self):
        cond = Condition("field", ConditionType.IN, ["a", "b", "c"])
        assert cond.evaluate({"field": "b"}) is True
        assert cond.evaluate({"field": "d"}) is False

    def test_contains_condition(self):
        cond = Condition("field", ConditionType.CONTAINS, "needle")
        assert cond.evaluate({"field": "haystackneedlemore"}) is True
        assert cond.evaluate({"field": "no match"}) is False

    def test_greater_than_condition(self):
        cond = Condition("field", ConditionType.GREATER_THAN, 0.5)
        assert cond.evaluate({"field": 0.8}) is True
        assert cond.evaluate({"field": 0.3}) is False

    def test_less_than_condition(self):
        cond = Condition("field", ConditionType.LESS_THAN, 0.5)
        assert cond.evaluate({"field": 0.3}) is True
        assert cond.evaluate({"field": 0.8}) is False


class TestDefaultRules:
    """Test that DEFAULT_RULES are well-formed."""

    def test_default_rules_exist(self):
        assert len(DEFAULT_RULES) > 0

    def test_default_rules_have_names(self):
        for rule in DEFAULT_RULES:
            assert len(rule.name) > 0

    def test_default_rules_have_conditions(self):
        for rule in DEFAULT_RULES:
            assert len(rule.conditions) > 0

    def test_critical_urgency_rule_exists(self):
        names = [r.name for r in DEFAULT_RULES]
        assert "critical_urgency_escalation" in names

    def test_bug_reports_rule_exists(self):
        names = [r.name for r in DEFAULT_RULES]
        assert "bug_reports_to_support" in names


# ===========================================================================
# TeamAssignmentManager tests
# ===========================================================================

class TestTeamAssignmentManager:
    """Test TeamAssignmentManager.get_team_for_category() mapping."""

    def test_bug_maps_to_support(self):
        manager = TeamAssignmentManager()
        assert manager.get_team_for_category("bug") == "support"

    def test_feature_maps_to_product(self):
        manager = TeamAssignmentManager()
        assert manager.get_team_for_category("feature") == "product"

    def test_question_maps_to_support(self):
        manager = TeamAssignmentManager()
        assert manager.get_team_for_category("question") == "support"

    def test_complaint_maps_to_customer_success(self):
        manager = TeamAssignmentManager()
        assert manager.get_team_for_category("complaint") == "customer_success"

    def test_praise_maps_to_customer_success(self):
        manager = TeamAssignmentManager()
        assert manager.get_team_for_category("praise") == "customer_success"

    def test_suggestion_maps_to_product(self):
        manager = TeamAssignmentManager()
        assert manager.get_team_for_category("suggestion") == "product"

    def test_lost_maps_to_sales(self):
        manager = TeamAssignmentManager()
        assert manager.get_team_for_category("lost") == "sales"

    def test_escalation_maps_to_management(self):
        manager = TeamAssignmentManager()
        assert manager.get_team_for_category("escalation") == "management"

    def test_unknown_category_defaults_to_support(self):
        manager = TeamAssignmentManager()
        assert manager.get_team_for_category("nonexistent_category") == "support"

    def test_get_team_for_critical_urgency(self):
        manager = TeamAssignmentManager()
        assert manager.get_team_for_urgency("critical") == "management"

    def test_get_team_for_non_critical_urgency(self):
        manager = TeamAssignmentManager()
        assert manager.get_team_for_urgency("high") is None

    def test_is_team_available(self):
        manager = TeamAssignmentManager()
        assert manager.is_team_available("sales") is True
        assert manager.is_team_available("nonexistent_team") is False

    def test_get_backup_team(self):
        manager = TeamAssignmentManager()
        assert manager.get_backup_team("sales") == "customer_success"
        assert manager.get_backup_team("support") == "customer_success"
        assert manager.get_backup_team("product") == "support"
        assert manager.get_backup_team("customer_success") == "support"

    def test_get_team_config(self):
        manager = TeamAssignmentManager()
        config = manager.get_team_config("sales")
        assert config is not None
        assert config.name == "Sales"

    def test_get_all_teams(self):
        manager = TeamAssignmentManager()
        all_teams = manager.get_all_teams()
        assert "sales" in all_teams
        assert "support" in all_teams
        assert "product" in all_teams
        assert "customer_success" in all_teams
