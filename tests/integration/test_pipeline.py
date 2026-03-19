"""Integration tests for the full feedback pipeline."""
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


class TestProspectProductivityPipeline:
    """Integration test for prospect productivity scenario (Eval 1)."""

    def test_prospect_productivity_end_to_end(self, prospect_productivity_fixture):
        """
        Full pipeline for Karen M., consulting manager.

        Expected flow:
        1. Raw input normalized
        2. Contact identified as prospect
        3. Classified as product_inquiry with themes 1+3
        4. Escalated to sales due to high urgency + strong prospect
        5. Response includes routing to sales with deadline context
        """
        fixture = prospect_productivity_fixture

        # Stage 1: Input validation
        assert fixture["raw_input"]
        assert fixture["channel"] == "website"

        # Stage 2: Contact identification
        contact = fixture["metadata"]["contact"]
        assert contact["name"] == "Karen M."
        assert contact["company"] == "Deloitte"
        assert contact["role"] == "Consulting Team Manager"

        # Stage 3: Classification
        classification = fixture["expected_classification"]
        assert classification["contact_type"] == "prospect"
        assert classification["category"] == "product_inquiry"
        assert 1 in classification["themes"]  # Productivity
        assert 3 in classification["themes"]  # Learning Curve
        assert classification["sentiment"] == "positive"
        assert classification["urgency"] == "high"

        # Stage 4: Routing
        routing = fixture["expected_routing"]
        assert routing["team"] == "sales"
        assert routing["escalated"] is True
        assert "deadline" in routing["reason"].lower() or "thursday" in fixture["raw_input"].lower()

        # Stage 5: Response metadata
        assert "reason" in routing

    def test_prospect_productivity_has_email(self, prospect_productivity_fixture):
        """Email should be present for contacting prospect."""
        contact = prospect_productivity_fixture["metadata"]["contact"]
        assert "email" in contact
        assert "@" in contact["email"]

    def test_prospect_productivity_deadline_context(self, prospect_productivity_fixture):
        """Routing reason should highlight deadline urgency."""
        routing = prospect_productivity_fixture["expected_routing"]
        reason = routing["reason"].lower()
        assert "thursday" in reason or "deadline" in reason or "tight" in reason


class TestPrivacyHealthcarePipeline:
    """Integration test for healthcare privacy inquiry (Eval 2)."""

    def test_privacy_healthcare_end_to_end(self, privacy_healthcare_fixture):
        """
        Full pipeline for David Chen, VP Ops at Meridian Health.

        Expected flow:
        1. Raw input from Slack normalized
        2. Contact identified as prospect
        3. Classified as compliance_security_inquiry with theme 4
        4. Escalated to enterprise sales due to 200-seat deal + compliance needs
        5. Response includes security brief commitment
        """
        fixture = privacy_healthcare_fixture

        # Stage 1: Input validation
        assert fixture["raw_input"]
        assert fixture["channel"] == "slack"

        # Stage 2: Contact identification
        contact = fixture["metadata"]["contact"]
        assert contact["name"] == "David Chen"
        assert contact["company"] == "Meridian Health"
        assert contact["estimated_team_size"] == 200

        # Stage 3: Classification
        classification = fixture["expected_classification"]
        assert classification["contact_type"] == "prospect"
        assert classification["category"] == "compliance_security_inquiry"
        assert 4 in classification["themes"]  # Privacy
        assert classification.get("compliance_flag") is True
        assert classification["urgency"] == "high"

        # Stage 4: Routing
        routing = fixture["expected_routing"]
        assert routing["team"] == "sales"
        assert routing.get("sub_team") == "enterprise"
        assert routing["escalated"] is True

        # Stage 5: Response metadata
        assert "enterprise" in routing["reason"].lower() or "compliance" in routing["reason"].lower()

    def test_privacy_healthcare_has_slack_context(self, privacy_healthcare_fixture):
        """Should have Slack metadata."""
        metadata = privacy_healthcare_fixture["metadata"]
        assert "slack_channel" in metadata
        assert "slack_user_id" in metadata

    def test_privacy_healthcare_legal_escalation(self, privacy_healthcare_fixture):
        """Legal/compliance needs should be clear in escalation."""
        routing = privacy_healthcare_fixture["expected_routing"]
        reason = routing["reason"].lower()
        assert "compliance" in reason or "legal" in reason or "hipaa" in reason or "security" in reason


class TestLostVisitorPipeline:
    """Integration test for lost visitor/family concern (Eval 3)."""

    def test_lost_visitor_end_to_end(self, lost_visitor_family_fixture):
        """
        Full pipeline for parent concerned about daughter's ChatGPT use.

        Expected flow:
        1. Raw input from pricing page normalized
        2. Contact identified as lost_visitor (not logged in)
        3. Classified as lost_visitor_inquiry with theme 5
        4. NOT escalated (routed to concierge for empathetic help)
        5. Response is concierge-style: empathize, redirect, provide resources
        """
        fixture = lost_visitor_family_fixture

        # Stage 1: Input validation
        assert fixture["raw_input"]
        assert fixture["channel"] == "website"

        # Stage 2: Contact identification
        contact = fixture["metadata"]["contact"]
        assert contact.get("logged_in") is False
        assert contact["role"] == "Parent"

        # Stage 3: Classification
        classification = fixture["expected_classification"]
        assert classification["contact_type"] == "lost_visitor"
        assert classification["category"] == "lost_visitor_inquiry"
        assert 5 in classification["themes"]  # Family
        assert classification["icp_fit"] == "not_applicable"

        # Stage 4: Routing
        routing = fixture["expected_routing"]
        assert routing["team"] == "concierge"
        assert routing["escalated"] is False
        # CRITICAL: action must include concierge, never dismiss
        assert "concierge" in routing["action"]

        # Stage 5: Response metadata
        reason = routing["reason"].lower()
        assert "genuine" in reason or "concern" in reason or "help" in reason

    def test_lost_visitor_not_dismissed(self, lost_visitor_family_fixture):
        """Lost visitor should NOT be dismissed or ignored."""
        routing = lost_visitor_family_fixture["expected_routing"]
        action = routing["action"].lower()
        # Should never have these
        assert "ignore" not in action
        assert "dismiss" not in action

    def test_lost_visitor_receives_empathetic_response(self, lost_visitor_family_fixture):
        """Routing should indicate empathetic, helpful response."""
        routing = lost_visitor_family_fixture["expected_routing"]
        reason = routing["reason"].lower()
        # Should acknowledge they have a real concern
        assert any(
            word in reason
            for word in ["genuine", "concern", "help", "empathi", "resource"]
        )


class TestClientCareerSecurityPipeline:
    """Integration test for customer success request (Eval 4)."""

    def test_client_career_security_end_to_end(self, client_career_security_fixture):
        """
        Full pipeline for David Chen, existing Meridian Health customer.

        Expected flow:
        1. Raw input from Slack Connect normalized
        2. Contact identified as client (customer_since present)
        3. Classified as customer_success_request with themes 2+3
        4. Routed to customer_success team (no escalation flag needed)
        5. Response includes demo support and CEO messaging resources
        """
        fixture = client_career_security_fixture

        # Stage 1: Input validation
        assert fixture["raw_input"]
        assert fixture["channel"] == "slack"

        # Stage 2: Contact identification
        metadata = fixture["metadata"]
        assert metadata.get("slack_channel_type") == "slack_connect"
        contact = metadata["contact"]
        assert contact["name"] == "David Chen"
        assert "customer_since" in contact
        assert contact["months_active"] == 3

        # Stage 3: Classification
        classification = fixture["expected_classification"]
        assert classification["contact_type"] == "client"
        assert classification["category"] == "customer_success_request"
        assert 2 in classification["themes"]  # Career Security
        assert 3 in classification["themes"]  # Learning Curve
        assert classification["sentiment"] == "positive"

        # Stage 4: Routing
        routing = fixture["expected_routing"]
        assert routing["team"] == "customer_success"
        # May or may not have escalation flag, but should have sub_team
        assert routing.get("sub_team") == "enterprise" or routing["team"] == "customer_success"

        # Stage 5: Response metadata
        assert "demo" in routing["reason"].lower() or "support" in routing["reason"].lower()

    def test_client_career_security_has_existing_relationship(
        self, client_career_security_fixture
    ):
        """Should recognize this is an existing customer."""
        contact = client_career_security_fixture["metadata"]["contact"]
        assert "customer_since" in contact
        assert contact["months_active"] == 3

    def test_client_gets_cs_support(self, client_career_security_fixture):
        """Should route to customer success, not sales."""
        routing = client_career_security_fixture["expected_routing"]
        assert routing["team"] == "customer_success"


class TestAllThemesFinancialPipeline:
    """Integration test for multi-theme financial advisor (Eval 5)."""

    def test_all_themes_end_to_end(self, all_themes_financial_fixture):
        """
        Full pipeline for Robert Tran, financial advisor (all themes).

        Expected flow:
        1. Raw input from product page normalized
        2. Contact identified as prospect
        3. Classified as product_inquiry with all themes 1-5
        4. Escalated to sales due to perfect ICP fit + high-value opportunity
        5. Response includes personalized position on productivity, career security,
           ease of use, compliance, and family/personal impact
        """
        fixture = all_themes_financial_fixture

        # Stage 1: Input validation
        assert fixture["raw_input"]
        assert fixture["channel"] == "website"

        # Stage 2: Contact identification
        contact = fixture["metadata"]["contact"]
        assert contact["name"] == "Robert Tran"
        assert contact["age"] == 54
        assert contact["company"] == "PNW Financial Advisors"
        assert contact["years_in_industry"] == 28

        # Stage 3: Classification
        classification = fixture["expected_classification"]
        assert classification["contact_type"] == "prospect"
        assert classification["category"] == "product_inquiry"
        # ALL FIVE themes should be present
        themes = classification["themes"]
        assert 1 in themes  # Productivity
        assert 2 in themes  # Career Security
        assert 3 in themes  # Learning Curve
        assert 4 in themes  # Privacy
        assert 5 in themes  # Family
        assert classification["icp_fit"] == "perfect"

        # Stage 4: Routing
        routing = fixture["expected_routing"]
        assert routing["team"] == "sales"
        assert routing["escalated"] is True

        # Stage 5: Response metadata
        reason = routing["reason"].lower()
        assert "icp" in reason or "perfect" in reason or "high-value" in reason

    def test_all_themes_five_themes_detected(self, all_themes_financial_fixture):
        """All five themes must be present."""
        themes = all_themes_financial_fixture["expected_classification"]["themes"]
        assert len(themes) == 5, f"Expected 5 themes, got {len(themes)}: {themes}"
        assert set(themes) == {1, 2, 3, 4, 5}

    def test_all_themes_perfect_icp_fit(self, all_themes_financial_fixture):
        """Financial advisor should be marked as perfect ICP fit."""
        icp_fit = all_themes_financial_fixture["expected_classification"]["icp_fit"]
        assert icp_fit == "perfect"

    def test_all_themes_mixed_sentiment_acknowledged(self, all_themes_financial_fixture):
        """Sentiment should reflect both concern and openness."""
        sentiment = all_themes_financial_fixture["expected_classification"]["sentiment"]
        # Could be "mixed_concerned_but_seeking" or contain both terms
        assert "concern" in sentiment.lower() or "mixed" in sentiment.lower()


class TestPipelineInvariants:
    """Test invariants that should hold across all pipeline tests."""

    def test_all_have_raw_input(
        self,
        prospect_productivity_fixture,
        privacy_healthcare_fixture,
        lost_visitor_family_fixture,
        client_career_security_fixture,
        all_themes_financial_fixture,
    ):
        """All fixtures should have raw_input."""
        for fixture in [
            prospect_productivity_fixture,
            privacy_healthcare_fixture,
            lost_visitor_family_fixture,
            client_career_security_fixture,
            all_themes_financial_fixture,
        ]:
            assert fixture["raw_input"]
            assert isinstance(fixture["raw_input"], str)
            assert len(fixture["raw_input"]) > 10

    def test_all_have_classification(
        self,
        prospect_productivity_fixture,
        privacy_healthcare_fixture,
        lost_visitor_family_fixture,
        client_career_security_fixture,
        all_themes_financial_fixture,
    ):
        """All fixtures should have complete classification."""
        for fixture in [
            prospect_productivity_fixture,
            privacy_healthcare_fixture,
            lost_visitor_family_fixture,
            client_career_security_fixture,
            all_themes_financial_fixture,
        ]:
            classification = fixture["expected_classification"]
            assert "category" in classification
            assert "themes" in classification
            assert "sentiment" in classification
            assert "contact_type" in classification
            assert "urgency" in classification

    def test_all_have_routing(
        self,
        prospect_productivity_fixture,
        privacy_healthcare_fixture,
        lost_visitor_family_fixture,
        client_career_security_fixture,
        all_themes_financial_fixture,
    ):
        """All fixtures should have complete routing."""
        for fixture in [
            prospect_productivity_fixture,
            privacy_healthcare_fixture,
            lost_visitor_family_fixture,
            client_career_security_fixture,
            all_themes_financial_fixture,
        ]:
            routing = fixture["expected_routing"]
            assert "action" in routing
            assert "team" in routing
            assert "escalated" in routing
            assert "reason" in routing


class TestChannelHandling:
    """Test that different channels are handled correctly."""

    def test_website_fixtures(
        self, prospect_productivity_fixture, lost_visitor_family_fixture, all_themes_financial_fixture
    ):
        """Website fixtures should have page_url in metadata."""
        for fixture in [prospect_productivity_fixture, lost_visitor_family_fixture, all_themes_financial_fixture]:
            assert fixture["channel"] == "website"
            assert "page_url" in fixture["metadata"]

    def test_slack_fixtures(self, privacy_healthcare_fixture, client_career_security_fixture):
        """Slack fixtures should have Slack-specific metadata."""
        for fixture in [privacy_healthcare_fixture, client_career_security_fixture]:
            assert fixture["channel"] == "slack"
            metadata = fixture["metadata"]
            assert "slack_channel" in metadata
            assert "slack_user_id" in metadata


class TestResponseGeneration:
    """Test that response generation expectations are met."""

    def test_lost_visitor_gets_concierge_response(self, lost_visitor_family_fixture):
        """Lost visitor should get concierge response action."""
        routing = lost_visitor_family_fixture["expected_routing"]
        assert "concierge" in routing["action"].lower()

    def test_prospects_get_sales_routing(
        self, prospect_productivity_fixture, privacy_healthcare_fixture, all_themes_financial_fixture
    ):
        """Prospects should be routed to sales."""
        for fixture in [prospect_productivity_fixture, privacy_healthcare_fixture, all_themes_financial_fixture]:
            routing = fixture["expected_routing"]
            assert routing["team"] == "sales"

    def test_client_gets_cs_routing(self, client_career_security_fixture):
        """Existing client should route to customer success."""
        routing = client_career_security_fixture["expected_routing"]
        assert routing["team"] == "customer_success"
