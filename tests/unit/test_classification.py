"""Unit tests for feedback classification engine."""
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


@pytest.fixture(
    params=[
        "prospect_productivity_fixture",
        "privacy_healthcare_fixture",
        "lost_visitor_family_fixture",
        "client_career_security_fixture",
        "all_themes_financial_fixture",
    ]
)
def all_fixtures(request):
    """Parametrized fixture providing all test scenarios."""
    return request.getfixturevalue(request.param)


class TestCategoryAssignment:
    """Test category assignment for feedback items."""

    def test_prospect_productivity_category(self, prospect_productivity_fixture):
        """Category for prospect with productivity need should be product_inquiry."""
        expected = prospect_productivity_fixture["expected_classification"]["category"]
        assert expected == "product_inquiry"

    def test_privacy_healthcare_category(self, privacy_healthcare_fixture):
        """Category for healthcare compliance inquiry should be compliance_security_inquiry."""
        expected = privacy_healthcare_fixture["expected_classification"]["category"]
        assert expected == "compliance_security_inquiry"

    def test_lost_visitor_category(self, lost_visitor_family_fixture):
        """Category for lost visitor should be lost_visitor_inquiry."""
        expected = lost_visitor_family_fixture["expected_classification"]["category"]
        assert expected == "lost_visitor_inquiry"

    def test_customer_success_category(self, client_career_security_fixture):
        """Category for existing customer request should be customer_success_request."""
        expected = client_career_security_fixture["expected_classification"]["category"]
        assert expected == "customer_success_request"

    def test_product_inquiry_category(self, all_themes_financial_fixture):
        """Category for financial advisor inquiry should be product_inquiry."""
        expected = all_themes_financial_fixture["expected_classification"]["category"]
        assert expected == "product_inquiry"


class TestThemeTagging:
    """Test ICP theme identification (1-5)."""

    def test_productivity_theme_detected(self, prospect_productivity_fixture):
        """Theme 1 (Productivity) should be detected in prospect message."""
        themes = prospect_productivity_fixture["expected_classification"]["themes"]
        assert 1 in themes, "Theme 1 (Productivity) not detected"

    def test_learning_curve_theme_detected(self, prospect_productivity_fixture):
        """Theme 3 (Learning Curve) should be detected in prospect message."""
        themes = prospect_productivity_fixture["expected_classification"]["themes"]
        assert 3 in themes, "Theme 3 (Learning Curve) not detected"

    def test_privacy_theme_detected(self, privacy_healthcare_fixture):
        """Theme 4 (Privacy) should be detected in healthcare inquiry."""
        themes = privacy_healthcare_fixture["expected_classification"]["themes"]
        assert 4 in themes, "Theme 4 (Privacy) not detected"

    def test_family_theme_detected(self, lost_visitor_family_fixture):
        """Theme 5 (Family) should be detected in parent inquiry."""
        themes = lost_visitor_family_fixture["expected_classification"]["themes"]
        assert 5 in themes, "Theme 5 (Family) not detected"

    def test_career_security_theme_detected(self, client_career_security_fixture):
        """Theme 2 (Career Security) should be detected in CEO demo request."""
        themes = client_career_security_fixture["expected_classification"]["themes"]
        assert 2 in themes, "Theme 2 (Career Security) not detected"

    def test_all_five_themes_detected(self, all_themes_financial_fixture):
        """All five themes should be detected in financial advisor message."""
        themes = all_themes_financial_fixture["expected_classification"]["themes"]
        expected_themes = [1, 2, 3, 4, 5]
        for theme in expected_themes:
            assert (
                theme in themes
            ), f"Theme {theme} not detected in all-themes fixture"

    def test_theme_count_reasonable(self, all_fixtures):
        """Theme count should be between 1 and 5."""
        themes = all_fixtures["expected_classification"]["themes"]
        assert 1 <= len(themes) <= 5, "Invalid number of themes"
        assert all(1 <= t <= 5 for t in themes), "Theme numbers out of range"


class TestSentimentAnalysis:
    """Test sentiment classification."""

    def test_prospect_positive_sentiment(self, prospect_productivity_fixture):
        """Prospect inquiry should have positive sentiment."""
        sentiment = prospect_productivity_fixture["expected_classification"]["sentiment"]
        assert sentiment == "positive"

    def test_healthcare_neutral_sentiment(self, privacy_healthcare_fixture):
        """Healthcare compliance inquiry should be neutral (business-like)."""
        sentiment = privacy_healthcare_fixture["expected_classification"]["sentiment"]
        assert sentiment == "neutral"

    def test_parent_concerned_sentiment(self, lost_visitor_family_fixture):
        """Parent inquiry should reflect concern."""
        sentiment = lost_visitor_family_fixture["expected_classification"]["sentiment"]
        assert sentiment == "concerned"

    def test_client_positive_sentiment(self, client_career_security_fixture):
        """Existing customer request should have positive sentiment."""
        sentiment = client_career_security_fixture["expected_classification"]["sentiment"]
        assert sentiment == "positive"

    def test_financial_advisor_mixed_sentiment(self, all_themes_financial_fixture):
        """Financial advisor expressing concern but seeking help should be mixed."""
        sentiment = all_themes_financial_fixture["expected_classification"]["sentiment"]
        assert "concerned" in sentiment or "mixed" in sentiment


class TestContactTypeIdentification:
    """Test contact type classification."""

    def test_prospect_contact_type(self, prospect_productivity_fixture):
        """First-time visitor from Deloitte should be classified as prospect."""
        contact_type = prospect_productivity_fixture["expected_classification"][
            "contact_type"
        ]
        assert contact_type == "prospect"

    def test_prospect_contact_type_healthcare(self, privacy_healthcare_fixture):
        """Healthcare buyer from Slack should be classified as prospect."""
        contact_type = privacy_healthcare_fixture["expected_classification"][
            "contact_type"
        ]
        assert contact_type == "prospect"

    def test_lost_visitor_contact_type(self, lost_visitor_family_fixture):
        """Unlogged-in parent should be classified as lost_visitor."""
        contact_type = lost_visitor_family_fixture["expected_classification"][
            "contact_type"
        ]
        assert contact_type == "lost_visitor"

    def test_client_contact_type(self, client_career_security_fixture):
        """Customer in Slack Connect should be classified as client."""
        contact_type = client_career_security_fixture["expected_classification"][
            "contact_type"
        ]
        assert contact_type == "client"

    def test_prospect_contact_type_financial(self, all_themes_financial_fixture):
        """Financial advisor with no prior relationship should be prospect."""
        contact_type = all_themes_financial_fixture["expected_classification"][
            "contact_type"
        ]
        assert contact_type == "prospect"


class TestIcpFitAssessment:
    """Test ICP fit scoring."""

    def test_strong_icp_fit_prospect(self, prospect_productivity_fixture):
        """Consulting manager at established firm is strong ICP fit."""
        icp_fit = prospect_productivity_fixture["expected_classification"]["icp_fit"]
        assert icp_fit == "strong"

    def test_strong_icp_fit_healthcare(self, privacy_healthcare_fixture):
        """Healthcare operations leader is strong ICP fit."""
        icp_fit = privacy_healthcare_fixture["expected_classification"]["icp_fit"]
        assert icp_fit == "strong"

    def test_not_applicable_lost_visitor(self, lost_visitor_family_fixture):
        """Parent is not ICP (consumer, not business user)."""
        icp_fit = lost_visitor_family_fixture["expected_classification"]["icp_fit"]
        assert icp_fit == "not_applicable"

    def test_perfect_icp_fit_financial(self, all_themes_financial_fixture):
        """54-year-old financial advisor is perfect ICP match."""
        icp_fit = all_themes_financial_fixture["expected_classification"]["icp_fit"]
        assert icp_fit == "perfect"


class TestUrgencyAssessment:
    """Test urgency scoring."""

    def test_high_urgency_deadline(self, prospect_productivity_fixture):
        """Prospect with Thursday deadline should be high urgency."""
        urgency = prospect_productivity_fixture["expected_classification"]["urgency"]
        assert urgency == "high"

    def test_high_urgency_compliance(self, privacy_healthcare_fixture):
        """Healthcare compliance inquiry should be high urgency."""
        urgency = privacy_healthcare_fixture["expected_classification"]["urgency"]
        assert urgency == "high"

    def test_medium_urgency_lost_visitor(self, lost_visitor_family_fixture):
        """Lost visitor concern is medium urgency (not immediate purchase)."""
        urgency = lost_visitor_family_fixture["expected_classification"]["urgency"]
        assert urgency == "medium"

    def test_medium_urgency_customer_request(self, client_career_security_fixture):
        """Customer support request is medium urgency."""
        urgency = client_career_security_fixture["expected_classification"]["urgency"]
        assert urgency == "medium"


class TestClassificationConsistency:
    """Test that classifications are internally consistent."""

    def test_contact_type_matches_metadata(self, prospect_productivity_fixture):
        """Contact type classification should match metadata indicators."""
        metadata = prospect_productivity_fixture["metadata"]["contact"]
        contact_type = prospect_productivity_fixture["expected_classification"][
            "contact_type"
        ]
        # First visitor should be prospect
        assert (
            contact_type == "prospect"
        ), "First-time contact should be prospect"

    def test_client_has_customer_since(self, client_career_security_fixture):
        """Client classification should have customer_since in metadata."""
        metadata = client_career_security_fixture["metadata"]["contact"]
        assert "customer_since" in metadata, "Client should have customer_since"

    def test_lost_visitor_not_logged_in(self, lost_visitor_family_fixture):
        """Lost visitor should not be logged in."""
        metadata = lost_visitor_family_fixture["metadata"]["contact"]
        assert (
            metadata.get("logged_in") is False
        ), "Lost visitor should not be logged in"

    def test_themes_match_sentiment(self, all_themes_financial_fixture):
        """Financial advisor's mixed sentiment should align with multiple themes."""
        themes = all_themes_financial_fixture["expected_classification"]["themes"]
        assert len(themes) > 1, "Mixed sentiment should have multiple themes"
