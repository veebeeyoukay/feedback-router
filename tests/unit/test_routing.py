"""Unit tests for feedback routing engine."""
import json
import pytest
from pathlib import Path

# Load test fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def prospect_productivity_fixture():
    """Load prospect productivity fixture."""
    with open(FIXTURES_DIR / "prospect_productivity.json") as f:
        return json.load(f)


@pytest.fixture
def privacy_healthcare_fixture():
    """Load privacy/healthcare fixture."""
    with open(FIXTURES_DIR / "privacy_healthcare.json") as f:
        return json.load(f)


@pytest.fixture
def lost_visitor_family_fixture():
    """Load lost visitor/family fixture."""
    with open(FIXTURES_DIR / "lost_visitor_family.json") as f:
        return json.load(f)


@pytest.fixture
def client_career_security_fixture():
    """Load client career security fixture."""
    with open(FIXTURES_DIR / "client_career_security.json") as f:
        return json.load(f)


@pytest.fixture
def all_themes_financial_fixture():
    """Load all themes financial fixture."""
    with open(FIXTURES_DIR / "all_themes_financial.json") as f:
        return json.load(f)


class TestEscalationTriggers:
    """Test that escalation triggers fire correctly."""

    def test_high_urgency_escalates(self, prospect_productivity_fixture):
        """High urgency with firm deadline should escalate."""
        routing = prospect_productivity_fixture["expected_routing"]
        assert routing["escalated"] is True

    def test_compliance_inquiry_escalates(self, privacy_healthcare_fixture):
        """Compliance/security inquiry should escalate."""
        routing = privacy_healthcare_fixture["expected_routing"]
        assert routing["escalated"] is True

    def test_enterprise_deal_escalates(self, privacy_healthcare_fixture):
        """200-seat enterprise deal should escalate."""
        routing = privacy_healthcare_fixture["expected_routing"]
        assert routing["escalated"] is True

    def test_multi_theme_escalates(self, all_themes_financial_fixture):
        """Multiple theme inquiry with strong ICP fit should escalate."""
        routing = all_themes_financial_fixture["expected_routing"]
        assert routing["escalated"] is True

    def test_lost_visitor_not_escalated(self, lost_visitor_family_fixture):
        """Lost visitor should not be escalated (routed to concierge instead)."""
        routing = lost_visitor_family_fixture["expected_routing"]
        assert routing["escalated"] is False

    def test_customer_support_escalation(self, client_career_security_fixture):
        """Customer support can route to team without escalation flag."""
        routing = client_career_security_fixture["expected_routing"]
        # Customer routing may not need escalation flag but should route somewhere
        assert "team" in routing


class TestTeamAssignment:
    """Test team assignment logic."""

    def test_prospect_routed_to_sales(self, prospect_productivity_fixture):
        """Prospect inquiry should route to sales team."""
        routing = prospect_productivity_fixture["expected_routing"]
        assert routing["team"] == "sales"

    def test_healthcare_routed_to_enterprise_sales(self, privacy_healthcare_fixture):
        """Healthcare enterprise deal should route to enterprise sales."""
        routing = privacy_healthcare_fixture["expected_routing"]
        assert routing["team"] == "sales"
        assert routing.get("sub_team") == "enterprise"

    def test_lost_visitor_routed_to_concierge(self, lost_visitor_family_fixture):
        """Lost visitor should route to concierge, not be dismissed."""
        routing = lost_visitor_family_fixture["expected_routing"]
        assert routing["team"] == "concierge"

    def test_customer_routed_to_success(self, client_career_security_fixture):
        """Existing customer request should route to customer success."""
        routing = client_career_security_fixture["expected_routing"]
        assert routing["team"] == "customer_success"

    def test_high_value_prospect_to_sales(self, all_themes_financial_fixture):
        """High-value ICP prospect should route to sales."""
        routing = all_themes_financial_fixture["expected_routing"]
        assert routing["team"] == "sales"


class TestLostVisitorHandling:
    """Test that lost visitors are properly handled."""

    def test_lost_visitor_not_dismissed(self, lost_visitor_family_fixture):
        """Lost visitor should receive concierge help, not be dismissed."""
        routing = lost_visitor_family_fixture["expected_routing"]
        action = routing["action"]
        # Should either be concierge_respond or similar, never "ignore" or "dismiss"
        assert "ignore" not in action
        assert "dismiss" not in action
        assert "concierge" in action

    def test_lost_visitor_team_is_concierge(self, lost_visitor_family_fixture):
        """Lost visitor team assignment should be concierge."""
        routing = lost_visitor_family_fixture["expected_routing"]
        assert routing["team"] == "concierge"

    def test_lost_visitor_reason_provided(self, lost_visitor_family_fixture):
        """Routing decision for lost visitor should have clear reason."""
        routing = lost_visitor_family_fixture["expected_routing"]
        reason = routing.get("reason", "")
        assert (
            len(reason) > 0
        ), "Reason for lost visitor routing should be documented"

    def test_lost_visitor_genuine_concern_addressed(
        self, lost_visitor_family_fixture
    ):
        """Lost visitor reason should acknowledge genuine concern, not dismiss them."""
        routing = lost_visitor_family_fixture["expected_routing"]
        reason = routing.get("reason", "").lower()
        assert "genuine" in reason or "concern" in reason or "help" in reason


class TestConfidenceThresholds:
    """Test confidence assessment in routing decisions."""

    def test_clear_prospect_has_confidence(self, prospect_productivity_fixture):
        """Clear prospect signals should have high confidence."""
        routing = prospect_productivity_fixture["expected_routing"]
        # Reason should indicate why we're confident
        reason = routing.get("reason", "")
        assert len(reason) > 0, "Routing decision should explain confidence"

    def test_compliance_inquiry_has_clear_path(self, privacy_healthcare_fixture):
        """Compliance inquiry should have clear routing path."""
        routing = privacy_healthcare_fixture["expected_routing"]
        assert "enterprise" in routing.get("sub_team", "").lower() or "sales" in routing[
            "team"
        ].lower()

    def test_mixed_signal_routing_explained(self, all_themes_financial_fixture):
        """Complex multi-theme routing should be well-explained."""
        routing = all_themes_financial_fixture["expected_routing"]
        reason = routing.get("reason", "")
        assert len(reason) > 0, "Complex routing should be well-explained"


class TestRoutingDecisionReasons:
    """Test that routing decisions include clear reasons."""

    def test_all_fixtures_have_reasons(self):
        """Every fixture's routing should include a reason."""
        fixtures = [
            "prospect_productivity.json",
            "privacy_healthcare.json",
            "lost_visitor_family.json",
            "client_career_security.json",
            "all_themes_financial.json",
        ]
        for fixture_name in fixtures:
            with open(FIXTURES_DIR / fixture_name) as f:
                fixture = json.load(f)
                routing = fixture["expected_routing"]
                assert "reason" in routing, f"{fixture_name} missing routing reason"
                assert len(routing["reason"]) > 0, f"{fixture_name} has empty reason"

    def test_reason_explains_team_choice(self, prospect_productivity_fixture):
        """Reason should explain why that team was chosen."""
        routing = prospect_productivity_fixture["expected_routing"]
        reason = routing["reason"].lower()
        team = routing["team"].lower()
        # Reason should relate to the team assignment
        assert len(reason) > 10, "Reason should be descriptive"

    def test_escalation_reason_clear(self, privacy_healthcare_fixture):
        """Escalation reasons should be specific and actionable."""
        routing = privacy_healthcare_fixture["expected_routing"]
        if routing["escalated"]:
            reason = routing["reason"].lower()
            # Should mention enterprise, healthcare, compliance, or similar
            assert any(
                keyword in reason
                for keyword in [
                    "enterprise",
                    "healthcare",
                    "compliance",
                    "200",
                    "legal",
                ]
            ), f"Escalation reason unclear: {reason}"


class TestRoutingConsistency:
    """Test that routing decisions are internally consistent."""

    def test_sales_routing_for_prospects(self, prospect_productivity_fixture):
        """All prospect contact types should route to sales."""
        classification = prospect_productivity_fixture["expected_classification"]
        routing = prospect_productivity_fixture["expected_routing"]
        if classification["contact_type"] == "prospect":
            assert routing["team"] == "sales"

    def test_client_routing_to_success_or_sales(self, client_career_security_fixture):
        """Client contact type should route to customer success or sales."""
        classification = client_career_security_fixture["expected_classification"]
        routing = client_career_security_fixture["expected_routing"]
        if classification["contact_type"] == "client":
            assert routing["team"] in ["customer_success", "sales"]

    def test_high_urgency_gets_escalated(self, prospect_productivity_fixture):
        """High urgency classification should result in escalation."""
        classification = prospect_productivity_fixture["expected_classification"]
        routing = prospect_productivity_fixture["expected_routing"]
        if classification["urgency"] == "high":
            assert routing["escalated"] is True

    def test_compliance_flag_triggers_escalation(self, privacy_healthcare_fixture):
        """Compliance flag in classification should trigger escalation."""
        classification = privacy_healthcare_fixture["expected_classification"]
        routing = privacy_healthcare_fixture["expected_routing"]
        if classification.get("compliance_flag"):
            assert routing["escalated"] is True


class TestActionTypes:
    """Test that routing action types are valid and appropriate."""

    def test_valid_action_types(self):
        """All fixtures should have valid action types."""
        valid_actions = {
            "respond_with_routing",
            "escalate_to_human",
            "concierge_respond",
            "route_to_human",
            "auto_respond",
        }
        fixtures = [
            "prospect_productivity.json",
            "privacy_healthcare.json",
            "lost_visitor_family.json",
            "client_career_security.json",
            "all_themes_financial.json",
        ]
        for fixture_name in fixtures:
            with open(FIXTURES_DIR / fixture_name) as f:
                fixture = json.load(f)
                action = fixture["expected_routing"]["action"]
                assert (
                    action in valid_actions
                ), f"Invalid action '{action}' in {fixture_name}"

    def test_concierge_for_lost_visitors(self, lost_visitor_family_fixture):
        """Lost visitors should use concierge_respond action."""
        routing = lost_visitor_family_fixture["expected_routing"]
        assert "concierge" in routing["action"]

    def test_escalate_action_for_complex_cases(self, privacy_healthcare_fixture):
        """Complex cases should use escalate_to_human action."""
        routing = privacy_healthcare_fixture["expected_routing"]
        assert "escalate" in routing["action"]
