"""Unit tests for classification modules: sentiment, themes, categories, contact."""

import pytest

from src.classification.sentiment import (
    analyze_sentiment,
    detect_urgency,
    PolarityEnum,
    UrgencyEnum,
)
from src.classification.themes import (
    tag_themes,
    get_theme_definition,
    get_all_themes,
    ThemeEnum,
)
from src.classification.categories import (
    get_category_definition,
    get_all_categories,
    CategoryEnum,
)
from src.classification.contact import ContactIdentifier, ContactTypeEnum


# ===========================================================================
# Sentiment Analysis tests
# ===========================================================================

class TestAnalyzeSentiment:
    """Test analyze_sentiment() function."""

    def test_positive_text(self):
        polarity, intensity, urgency = analyze_sentiment(
            "I love this product! It's amazing and excellent."
        )
        assert polarity == PolarityEnum.POSITIVE
        assert intensity > 0.3

    def test_negative_text(self):
        polarity, intensity, urgency = analyze_sentiment(
            "This is terrible. The product is broken and useless."
        )
        assert polarity == PolarityEnum.NEGATIVE
        assert intensity > 0.3

    def test_neutral_text(self):
        polarity, intensity, urgency = analyze_sentiment(
            "I submitted the document at 3pm on Tuesday."
        )
        assert polarity == PolarityEnum.NEUTRAL
        assert intensity == 0.5  # default for no signals

    def test_mixed_text(self):
        polarity, intensity, urgency = analyze_sentiment(
            "I love the design but hate the pricing."
        )
        assert polarity == PolarityEnum.MIXED

    def test_empty_text_returns_neutral(self):
        polarity, intensity, urgency = analyze_sentiment("")
        assert polarity == PolarityEnum.NEUTRAL
        assert intensity == 0.5
        assert urgency == UrgencyEnum.MEDIUM

    def test_intensifiers_boost_intensity(self):
        _, base_intensity, _ = analyze_sentiment("The product is great.")
        _, boosted_intensity, _ = analyze_sentiment("The product is really extremely great.")
        assert boosted_intensity > base_intensity

    def test_negative_intensifiers_boost_intensity(self):
        _, base_intensity, _ = analyze_sentiment("This is bad.")
        _, boosted_intensity, _ = analyze_sentiment("This is bad, never works, always crashes.")
        assert boosted_intensity > base_intensity

    def test_intensity_capped_at_one(self):
        # Pile on many signals and intensifiers
        text = " ".join([
            "love great awesome excellent amazing wonderful fantastic perfect best",
            "really very extremely incredibly absolutely totally completely",
        ])
        _, intensity, _ = analyze_sentiment(text)
        assert 0.0 <= intensity <= 1.0

    def test_intensity_minimum_zero(self):
        _, intensity, _ = analyze_sentiment("a")
        assert intensity >= 0.0

    def test_returns_tuple_of_three(self):
        result = analyze_sentiment("some text")
        assert len(result) == 3


class TestDetectUrgency:
    """Test detect_urgency() function."""

    def test_critical_urgency_signals(self):
        urgency = detect_urgency("this is a critical emergency", PolarityEnum.NEUTRAL, 0.5)
        assert urgency == UrgencyEnum.CRITICAL

    def test_security_is_critical(self):
        urgency = detect_urgency("there has been a security breach", PolarityEnum.NEGATIVE, 0.8)
        assert urgency == UrgencyEnum.CRITICAL

    def test_blocking_is_critical(self):
        urgency = detect_urgency("this is blocking our release", PolarityEnum.NEGATIVE, 0.7)
        assert urgency == UrgencyEnum.CRITICAL

    def test_high_urgency_from_multiple_signals(self):
        urgency = detect_urgency(
            "this is important and must be done soon",
            PolarityEnum.NEUTRAL,
            0.5,
        )
        assert urgency == UrgencyEnum.HIGH

    def test_high_urgency_from_negative_intensity(self):
        urgency = detect_urgency(
            "the widget is a poor implementation",
            PolarityEnum.NEGATIVE,
            0.75,
        )
        assert urgency == UrgencyEnum.HIGH

    def test_medium_urgency_signals(self):
        urgency = detect_urgency(
            "it would be helpful if you could look into this",
            PolarityEnum.NEUTRAL,
            0.4,
        )
        assert urgency == UrgencyEnum.MEDIUM

    def test_low_urgency_default(self):
        urgency = detect_urgency(
            "just sharing some thoughts on the color scheme",
            PolarityEnum.POSITIVE,
            0.3,
        )
        assert urgency == UrgencyEnum.LOW

    def test_ceo_is_critical(self):
        urgency = detect_urgency("our ceo is asking about this", PolarityEnum.NEUTRAL, 0.5)
        assert urgency == UrgencyEnum.CRITICAL

    def test_asap_is_critical(self):
        urgency = detect_urgency("we need this fixed asap", PolarityEnum.NEGATIVE, 0.6)
        assert urgency == UrgencyEnum.CRITICAL


# ===========================================================================
# Theme detection tests
# ===========================================================================

class TestTagThemes:
    """Test tag_themes() function."""

    def test_pricing_theme(self):
        themes = tag_themes("Your pricing is too expensive. We can't afford this subscription.")
        assert "pricing_sensitivity" in themes

    def test_competitive_pressure_theme(self):
        themes = tag_themes("We are considering switching to a competitor.")
        assert "competitive_pressure" in themes

    def test_feature_parity_theme(self):
        themes = tag_themes("This feature is missing. We need this capability.")
        assert "feature_parity" in themes

    def test_implementation_friction_theme(self):
        themes = tag_themes("The setup was very difficult and the integration is complex.")
        assert "implementation_friction" in themes

    def test_support_expectations_theme(self):
        themes = tag_themes("Support response time is slow and the service is poor.")
        assert "support_expectations" in themes

    def test_multiple_themes_detected(self):
        themes = tag_themes(
            "The price is too expensive compared to competitors. Also the integration is difficult."
        )
        assert "pricing_sensitivity" in themes
        assert "competitive_pressure" in themes or "implementation_friction" in themes

    def test_empty_text_returns_empty(self):
        themes = tag_themes("")
        assert themes == []

    def test_no_themes_returns_empty(self):
        themes = tag_themes("I enjoyed the weather today.")
        assert themes == []

    def test_min_keyword_matches_parameter(self):
        # With a higher threshold, fewer themes should match
        themes_low = tag_themes("price cost budget", min_keyword_matches=1)
        themes_high = tag_themes("price cost budget", min_keyword_matches=5)
        assert len(themes_low) >= len(themes_high)

    def test_phrase_matches_weighted_higher(self):
        # Phrase like "too expensive" should count as 2 keyword matches
        themes = tag_themes("too expensive", min_keyword_matches=2)
        assert "pricing_sensitivity" in themes

    def test_themes_returned_sorted(self):
        themes = tag_themes(
            "price is too expensive, competitor offers better value, and your support is slow"
        )
        assert themes == sorted(themes)


class TestGetThemeDefinition:
    """Test get_theme_definition() function."""

    def test_returns_definition_for_each_theme(self):
        for theme in ThemeEnum:
            definition = get_theme_definition(theme)
            assert definition.name is not None
            assert len(definition.signal_keywords) > 0
            assert len(definition.signal_phrases) > 0

    def test_pricing_sensitivity_definition(self):
        definition = get_theme_definition(ThemeEnum.PRICING_SENSITIVITY)
        assert "pricing" in definition.name.lower() or "pricing" in definition.description.lower()
        assert "price" in definition.signal_keywords

    def test_invalid_theme_raises_error(self):
        with pytest.raises(KeyError):
            get_theme_definition("not_a_theme")


class TestGetAllThemes:
    """Test get_all_themes() function."""

    def test_returns_all_five_themes(self):
        all_themes = get_all_themes()
        assert len(all_themes) == 5

    def test_all_enum_values_present(self):
        all_themes = get_all_themes()
        for theme in ThemeEnum:
            assert theme in all_themes


# ===========================================================================
# Category definition tests
# ===========================================================================

class TestGetCategoryDefinition:
    """Test get_category_definition() function."""

    def test_returns_definition_for_each_category(self):
        for category in CategoryEnum:
            definition = get_category_definition(category)
            assert definition.name is not None
            assert len(definition.description) > 0
            assert len(definition.examples) > 0
            assert len(definition.keywords) > 0

    def test_bug_category_definition(self):
        definition = get_category_definition(CategoryEnum.BUG)
        assert "bug" in definition.keywords
        assert "error" in definition.keywords

    def test_feature_category_definition(self):
        definition = get_category_definition(CategoryEnum.FEATURE)
        assert "feature" in definition.keywords

    def test_complaint_category_definition(self):
        definition = get_category_definition(CategoryEnum.COMPLAINT)
        assert "frustrated" in definition.keywords or "complaint" in definition.keywords

    def test_escalation_category_definition(self):
        definition = get_category_definition(CategoryEnum.ESCALATION)
        assert "urgent" in definition.keywords or "critical" in definition.keywords

    def test_invalid_category_raises_error(self):
        with pytest.raises(KeyError):
            get_category_definition("not_a_category")


class TestGetAllCategories:
    """Test get_all_categories() function."""

    def test_returns_all_categories(self):
        all_categories = get_all_categories()
        assert len(all_categories) == len(CategoryEnum)

    def test_all_enum_values_present(self):
        all_categories = get_all_categories()
        for category in CategoryEnum:
            assert category in all_categories


# ===========================================================================
# Contact Identifier tests
# ===========================================================================

class TestContactIdentifier:
    """Test ContactIdentifier class."""

    def test_identify_prospect_by_default(self):
        identifier = ContactIdentifier()
        contact_type, contact_id, account_id = identifier.identify_contact(
            text="I'm interested in your product."
        )
        assert contact_type == ContactTypeEnum.PROSPECT

    def test_identify_client_by_account_id(self):
        identifier = ContactIdentifier()
        contact_type, contact_id, account_id = identifier.identify_contact(
            text="Some feedback",
            account_id="acct_123",
        )
        assert contact_type == ContactTypeEnum.CLIENT
        assert account_id == "acct_123"

    def test_identify_internal_from_text(self):
        identifier = ContactIdentifier()
        contact_type, _, _ = identifier.identify_contact(
            text="Our internal team has noticed performance issues."
        )
        assert contact_type == ContactTypeEnum.INTERNAL

    def test_identify_internal_from_colleague_text(self):
        identifier = ContactIdentifier()
        contact_type, _, _ = identifier.identify_contact(
            text="My colleague reported that the employee portal is broken."
        )
        assert contact_type == ContactTypeEnum.INTERNAL

    def test_identify_churned_from_churn_text(self):
        identifier = ContactIdentifier()
        contact_type, _, _ = identifier.identify_contact(
            text="We are going to cancel our subscription."
        )
        assert contact_type == ContactTypeEnum.CHURNED

    def test_identify_churned_from_switching_text(self):
        identifier = ContactIdentifier()
        contact_type, _, _ = identifier.identify_contact(
            text="We are switching to Competitor X."
        )
        assert contact_type == ContactTypeEnum.CHURNED

    def test_identify_known_email_from_database(self):
        contact_db = {
            "john@acme.com": {
                "type": ContactTypeEnum.CLIENT,
                "account_id": "acct_acme",
            }
        }
        identifier = ContactIdentifier(contact_db=contact_db)
        contact_type, contact_id, account_id = identifier.identify_contact(
            text="Some feedback",
            email="john@acme.com",
        )
        assert contact_type == ContactTypeEnum.CLIENT
        assert account_id == "acct_acme"

    def test_unknown_email_not_in_database(self):
        contact_db = {
            "known@acme.com": {"type": ContactTypeEnum.CLIENT, "account_id": "acct_1"},
        }
        identifier = ContactIdentifier(contact_db=contact_db)
        contact_type, _, _ = identifier.identify_contact(
            text="Hi, I saw your ad.",
            email="stranger@gmail.com",
        )
        assert contact_type == ContactTypeEnum.PROSPECT


class TestContactIdentifierExtractEmail:
    """Test ContactIdentifier.extract_email()."""

    def test_extract_email_simple(self):
        identifier = ContactIdentifier()
        email = identifier.extract_email("Please contact me at john@example.com for details.")
        assert email == "john@example.com"

    def test_extract_email_with_subdomain(self):
        identifier = ContactIdentifier()
        email = identifier.extract_email("Send to user@mail.company.co.uk")
        assert email == "user@mail.company.co.uk"

    def test_no_email_returns_none(self):
        identifier = ContactIdentifier()
        email = identifier.extract_email("No email here")
        assert email is None

    def test_extract_first_email_from_multiple(self):
        identifier = ContactIdentifier()
        email = identifier.extract_email("Reach me at a@b.com or c@d.com")
        assert email in ("a@b.com", "c@d.com")


class TestContactIdentifierExtractSlackHandle:
    """Test ContactIdentifier.extract_slack_handle()."""

    def test_extract_slack_handle(self):
        identifier = ContactIdentifier()
        handle = identifier.extract_slack_handle("Hey @john.doe can you check?")
        assert handle == "john.doe"

    def test_no_slack_handle_returns_none(self):
        identifier = ContactIdentifier()
        handle = identifier.extract_slack_handle("No handle in this text")
        assert handle is None

    def test_extract_handle_with_hyphens(self):
        identifier = ContactIdentifier()
        handle = identifier.extract_slack_handle("cc @user-name-123")
        assert handle == "user-name-123"
