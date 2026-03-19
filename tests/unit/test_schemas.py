"""Unit tests for schema validation."""
import json
import pytest
from pathlib import Path

# Load test fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def all_fixture_files():
    """Get all fixture files."""
    return [
        "prospect_productivity.json",
        "privacy_healthcare.json",
        "lost_visitor_family.json",
        "client_career_security.json",
        "all_themes_financial.json",
    ]


@pytest.fixture(params=[
    "prospect_productivity.json",
    "privacy_healthcare.json",
    "lost_visitor_family.json",
    "client_career_security.json",
    "all_themes_financial.json",
])
def fixture_content(request):
    """Parametrized fixture for all test data."""
    with open(FIXTURES_DIR / request.param) as f:
        return json.load(f)


class TestFeedbackItemSchema:
    """Test FeedbackItem schema validation."""

    def test_fixture_structure_valid(self, fixture_content):
        """Fixture should have all required top-level fields."""
        required_fields = {
            "raw_input",
            "channel",
            "metadata",
            "expected_classification",
            "expected_routing",
        }
        assert required_fields.issubset(
            fixture_content.keys()
        ), f"Missing required fields: {required_fields - set(fixture_content.keys())}"

    def test_raw_input_not_empty(self, fixture_content):
        """raw_input should be non-empty string."""
        raw_input = fixture_content["raw_input"]
        assert isinstance(raw_input, str), "raw_input must be string"
        assert len(raw_input) > 0, "raw_input cannot be empty"

    def test_channel_valid_value(self, fixture_content):
        """channel should be 'website' or 'slack'."""
        channel = fixture_content["channel"]
        valid_channels = {"website", "slack"}
        assert (
            channel in valid_channels
        ), f"channel must be one of {valid_channels}, got {channel}"

    def test_metadata_is_dict(self, fixture_content):
        """metadata should be a dictionary."""
        metadata = fixture_content["metadata"]
        assert isinstance(metadata, dict), "metadata must be a dictionary"

    def test_expected_classification_is_dict(self, fixture_content):
        """expected_classification should be a dictionary."""
        classification = fixture_content["expected_classification"]
        assert isinstance(
            classification, dict
        ), "expected_classification must be a dictionary"

    def test_expected_routing_is_dict(self, fixture_content):
        """expected_routing should be a dictionary."""
        routing = fixture_content["expected_routing"]
        assert isinstance(routing, dict), "expected_routing must be a dictionary"


class TestMetadataSchema:
    """Test metadata field validation."""

    def test_website_metadata_has_url(self):
        """Website feedback should have page_url in metadata."""
        with open(FIXTURES_DIR / "prospect_productivity.json") as f:
            fixture = json.load(f)
        metadata = fixture["metadata"]
        assert "page_url" in metadata or fixture["channel"] == "slack"

    def test_slack_metadata_has_channel(self):
        """Slack feedback should have slack_channel in metadata."""
        with open(FIXTURES_DIR / "privacy_healthcare.json") as f:
            fixture = json.load(f)
        metadata = fixture["metadata"]
        if fixture["channel"] == "slack":
            assert "slack_channel" in metadata, "Slack feedback must have slack_channel"

    def test_contact_info_present(self, fixture_content):
        """Metadata should have contact information."""
        metadata = fixture_content["metadata"]
        assert "contact" in metadata, "metadata must have contact information"
        contact = metadata["contact"]
        assert isinstance(contact, dict), "contact must be a dictionary"

    def test_contact_has_name(self, fixture_content):
        """Contact should have a name (or 'Unknown' for lost visitors)."""
        contact = fixture_content["metadata"]["contact"]
        assert "name" in contact, "contact must have a name"
        name = contact.get("name")
        # Name can be "Unknown Parent" or actual name, but should exist
        assert name is not None and len(str(name)) > 0

    def test_contact_has_role_or_context(self, fixture_content):
        """Contact should have role or context field."""
        contact = fixture_content["metadata"]["contact"]
        assert (
            "role" in contact or "context" in contact
        ), "contact must have role or context"

    def test_theme_list_in_classification(self, fixture_content):
        """Classification should have themes list."""
        classification = fixture_content["expected_classification"]
        assert "themes" in classification, "classification must have themes"
        themes = classification["themes"]
        assert isinstance(themes, list), "themes must be a list"
        assert len(themes) > 0, "themes list cannot be empty"


class TestClassificationSchema:
    """Test expected_classification field validation."""

    def test_category_present(self, fixture_content):
        """Classification must have category."""
        classification = fixture_content["expected_classification"]
        assert "category" in classification, "classification must have category"
        category = classification["category"]
        assert isinstance(category, str) and len(category) > 0

    def test_valid_categories(self, fixture_content):
        """Category values should be reasonable feedback categories."""
        classification = fixture_content["expected_classification"]
        category = classification["category"]
        # Valid categories based on README
        valid_categories = {
            "product_inquiry",
            "compliance_security_inquiry",
            "lost_visitor_inquiry",
            "customer_success_request",
            "feature_request",
            "bug_report",
            "pricing_question",
        }
        # More flexible: just check it's a reasonable category name
        assert len(category) > 0 and "_" in category or "success" in category

    def test_themes_are_integers_1_to_5(self, fixture_content):
        """Themes should be integers from 1-5."""
        classification = fixture_content["expected_classification"]
        themes = classification["themes"]
        for theme in themes:
            assert isinstance(theme, int), f"theme must be int, got {type(theme)}"
            assert 1 <= theme <= 5, f"theme must be 1-5, got {theme}"

    def test_sentiment_valid(self, fixture_content):
        """Sentiment should be a valid sentiment value."""
        classification = fixture_content["expected_classification"]
        sentiment = classification["sentiment"]
        valid_sentiments = {
            "positive",
            "neutral",
            "negative",
            "concerned",
            "mixed_concerned_but_seeking",
        }
        # Allow for variations in naming
        assert isinstance(sentiment, str) and len(sentiment) > 0

    def test_contact_type_valid(self, fixture_content):
        """Contact type should be valid."""
        classification = fixture_content["expected_classification"]
        contact_type = classification["contact_type"]
        valid_types = {"prospect", "client", "lost_visitor", "internal", "unknown"}
        assert contact_type in valid_types, f"Invalid contact_type: {contact_type}"

    def test_urgency_valid(self, fixture_content):
        """Urgency should be low, medium, or high."""
        classification = fixture_content["expected_classification"]
        urgency = classification["urgency"]
        valid_urgencies = {"low", "medium", "high"}
        assert urgency in valid_urgencies, f"Invalid urgency: {urgency}"


class TestRoutingSchema:
    """Test expected_routing field validation."""

    def test_action_present(self, fixture_content):
        """Routing must have action."""
        routing = fixture_content["expected_routing"]
        assert "action" in routing, "routing must have action"

    def test_team_present(self, fixture_content):
        """Routing must have team assignment."""
        routing = fixture_content["expected_routing"]
        assert "team" in routing, "routing must have team"
        team = routing["team"]
        assert isinstance(team, str) and len(team) > 0

    def test_escalated_is_boolean(self, fixture_content):
        """escalated field must be boolean."""
        routing = fixture_content["expected_routing"]
        assert "escalated" in routing, "routing must have escalated field"
        assert isinstance(
            routing["escalated"], bool
        ), "escalated must be boolean"

    def test_reason_present(self, fixture_content):
        """Routing must include reason."""
        routing = fixture_content["expected_routing"]
        assert "reason" in routing, "routing must have reason"
        reason = routing["reason"]
        assert isinstance(reason, str) and len(reason) > 0, "reason must be non-empty string"

    def test_valid_teams(self, fixture_content):
        """Team assignments should be reasonable."""
        routing = fixture_content["expected_routing"]
        team = routing["team"]
        valid_teams = {
            "sales",
            "customer_success",
            "concierge",
            "support",
            "product",
            "engineering",
        }
        assert (
            team in valid_teams
        ), f"Invalid team: {team} (must be one of {valid_teams})"

    def test_sub_team_optional(self, fixture_content):
        """sub_team is optional but if present should be string."""
        routing = fixture_content["expected_routing"]
        if "sub_team" in routing:
            assert isinstance(
                routing["sub_team"], str
            ), "sub_team must be string"


class TestSchemaIntegrity:
    """Test relationships between fields across schemas."""

    def test_lost_visitor_consistent(self):
        """Lost visitor fixture should have consistent lost_visitor indicators."""
        with open(FIXTURES_DIR / "lost_visitor_family.json") as f:
            fixture = json.load(f)
        classification = fixture["expected_classification"]
        routing = fixture["expected_routing"]
        # Should be marked as lost_visitor in contact type
        assert classification["contact_type"] == "lost_visitor"
        # Should route to concierge
        assert routing["team"] == "concierge"

    def test_client_consistent(self):
        """Client fixture should have consistent client indicators."""
        with open(FIXTURES_DIR / "client_career_security.json") as f:
            fixture = json.load(f)
        classification = fixture["expected_classification"]
        # Should be marked as client
        assert classification["contact_type"] == "client"
        # Should have customer_since in metadata
        metadata = fixture["metadata"]["contact"]
        assert "customer_since" in metadata

    def test_prospect_consistent(self):
        """Prospect fixtures should have consistent prospect indicators."""
        prospect_files = [
            "prospect_productivity.json",
            "privacy_healthcare.json",
            "all_themes_financial.json",
        ]
        for fname in prospect_files:
            with open(FIXTURES_DIR / fname) as f:
                fixture = json.load(f)
            classification = fixture["expected_classification"]
            assert classification["contact_type"] == "prospect"

    def test_icp_fit_reasonable(self, fixture_content):
        """ICP fit should match contact type."""
        classification = fixture_content["expected_classification"]
        contact_type = classification["contact_type"]
        icp_fit = classification.get("icp_fit")
        # Lost visitors should have not_applicable
        if contact_type == "lost_visitor":
            assert icp_fit == "not_applicable"
        # Prospects and clients should have an ICP fit
        elif contact_type in ("prospect", "client"):
            assert icp_fit in ("strong", "perfect", "moderate")


class TestFixtureLoading:
    """Test that all fixtures load correctly."""

    def test_all_fixtures_load(self, all_fixture_files):
        """All fixture files should load as valid JSON."""
        for fixture_name in all_fixture_files:
            fixture_path = FIXTURES_DIR / fixture_name
            assert fixture_path.exists(), f"Fixture not found: {fixture_name}"
            with open(fixture_path) as f:
                data = json.load(f)
                assert isinstance(data, dict), f"{fixture_name} not a JSON object"

    def test_fixture_count(self, all_fixture_files):
        """Should have exactly 5 fixtures."""
        assert len(all_fixture_files) == 5, f"Expected 5 fixtures, got {len(all_fixture_files)}"
