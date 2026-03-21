"""Unit tests for all Pydantic schema models in src/schemas/."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.schemas.feedback import (
    FeedbackItem,
    FeedbackSource,
    FeedbackSourceEnum,
    FeedbackContact,
    ContactTypeEnum,
    FeedbackContent,
    FeedbackClassification,
    FeedbackRouting,
    FeedbackResponse,
    FeedbackLifecycle,
    FeedbackStatusEnum,
    SentimentScore,
    PolarityEnum,
    UrgencyEnum,
    CategoryEnum,
    ResponseTypeEnum,
)
from src.schemas.classification import ClassificationRequest, ClassificationOutput
from src.schemas.routing import RoutingRequest, RoutingDecision
from src.schemas.response import ResponseRequest, ResponseOutput


# ---------------------------------------------------------------------------
# FeedbackSource tests
# ---------------------------------------------------------------------------

class TestFeedbackSource:
    """Test FeedbackSource model."""

    def test_creation_with_all_fields(self):
        source = FeedbackSource(
            channel=FeedbackSourceEnum.WEBSITE_FORM,
            platform="contact_form_v1",
            raw_id="form_12345",
            context={"page_url": "https://example.com/pricing"},
        )
        assert source.channel == FeedbackSourceEnum.WEBSITE_FORM
        assert source.platform == "contact_form_v1"
        assert source.raw_id == "form_12345"
        assert source.context == {"page_url": "https://example.com/pricing"}

    def test_creation_with_minimal_fields(self):
        source = FeedbackSource(
            channel=FeedbackSourceEnum.SLACK,
            raw_id="slack_msg_001",
        )
        assert source.channel == FeedbackSourceEnum.SLACK
        assert source.platform is None
        assert source.context == {}

    def test_all_channel_enum_values(self):
        for channel in FeedbackSourceEnum:
            source = FeedbackSource(channel=channel, raw_id="test")
            assert source.channel == channel

    def test_invalid_channel_raises_error(self):
        with pytest.raises(ValidationError):
            FeedbackSource(channel="invalid_channel", raw_id="test")

    def test_missing_required_channel_raises_error(self):
        with pytest.raises(ValidationError):
            FeedbackSource(raw_id="test")

    def test_missing_required_raw_id_raises_error(self):
        with pytest.raises(ValidationError):
            FeedbackSource(channel=FeedbackSourceEnum.EMAIL)


# ---------------------------------------------------------------------------
# FeedbackContact tests
# ---------------------------------------------------------------------------

class TestFeedbackContact:
    """Test FeedbackContact model."""

    def test_creation_with_all_fields(self):
        contact = FeedbackContact(
            type=ContactTypeEnum.PROSPECT,
            id="cont_123",
            name="John Doe",
            account="acct_456",
            history={"previous_inquiries": 2},
        )
        assert contact.type == ContactTypeEnum.PROSPECT
        assert contact.id == "cont_123"
        assert contact.name == "John Doe"
        assert contact.account == "acct_456"
        assert contact.history == {"previous_inquiries": 2}

    def test_creation_with_minimal_fields(self):
        contact = FeedbackContact(type=ContactTypeEnum.UNKNOWN)
        assert contact.type == ContactTypeEnum.UNKNOWN
        assert contact.id is None
        assert contact.name is None
        assert contact.account is None
        assert contact.history == {}

    def test_all_contact_type_enum_values(self):
        for contact_type in ContactTypeEnum:
            contact = FeedbackContact(type=contact_type)
            assert contact.type == contact_type

    def test_invalid_contact_type_raises_error(self):
        with pytest.raises(ValidationError):
            FeedbackContact(type="invalid_type")


# ---------------------------------------------------------------------------
# FeedbackContent tests
# ---------------------------------------------------------------------------

class TestFeedbackContent:
    """Test FeedbackContent model."""

    def test_creation_with_all_fields(self):
        content = FeedbackContent(
            raw_text="Your pricing is too high",
            summary="Customer concerned about pricing",
            language="en",
        )
        assert content.raw_text == "Your pricing is too high"
        assert content.summary == "Customer concerned about pricing"
        assert content.language == "en"

    def test_creation_with_minimal_fields(self):
        content = FeedbackContent(raw_text="Some feedback")
        assert content.raw_text == "Some feedback"
        assert content.summary is None
        assert content.language == "en"  # default

    def test_missing_raw_text_raises_error(self):
        with pytest.raises(ValidationError):
            FeedbackContent()


# ---------------------------------------------------------------------------
# SentimentScore tests
# ---------------------------------------------------------------------------

class TestSentimentScore:
    """Test SentimentScore model."""

    def test_creation_with_valid_values(self):
        score = SentimentScore(
            polarity=PolarityEnum.NEGATIVE,
            intensity=0.85,
            urgency=UrgencyEnum.HIGH,
        )
        assert score.polarity == PolarityEnum.NEGATIVE
        assert score.intensity == 0.85
        assert score.urgency == UrgencyEnum.HIGH

    def test_intensity_at_boundaries(self):
        low = SentimentScore(polarity=PolarityEnum.NEUTRAL, intensity=0.0, urgency=UrgencyEnum.LOW)
        assert low.intensity == 0.0

        high = SentimentScore(polarity=PolarityEnum.NEUTRAL, intensity=1.0, urgency=UrgencyEnum.LOW)
        assert high.intensity == 1.0

    def test_intensity_above_one_raises_error(self):
        with pytest.raises(ValidationError):
            SentimentScore(polarity=PolarityEnum.NEUTRAL, intensity=1.1, urgency=UrgencyEnum.LOW)

    def test_intensity_below_zero_raises_error(self):
        with pytest.raises(ValidationError):
            SentimentScore(polarity=PolarityEnum.NEUTRAL, intensity=-0.1, urgency=UrgencyEnum.LOW)

    def test_all_polarity_values(self):
        for polarity in PolarityEnum:
            score = SentimentScore(polarity=polarity, intensity=0.5, urgency=UrgencyEnum.MEDIUM)
            assert score.polarity == polarity

    def test_all_urgency_values(self):
        for urgency in UrgencyEnum:
            score = SentimentScore(polarity=PolarityEnum.NEUTRAL, intensity=0.5, urgency=urgency)
            assert score.urgency == urgency

    def test_invalid_polarity_raises_error(self):
        with pytest.raises(ValidationError):
            SentimentScore(polarity="very_bad", intensity=0.5, urgency=UrgencyEnum.LOW)


# ---------------------------------------------------------------------------
# FeedbackClassification tests
# ---------------------------------------------------------------------------

class TestFeedbackClassification:
    """Test FeedbackClassification model."""

    def test_creation_with_all_fields(self):
        classification = FeedbackClassification(
            category=CategoryEnum.COMPLAINT,
            subcategory="pricing",
            sentiment=SentimentScore(
                polarity=PolarityEnum.NEGATIVE,
                intensity=0.75,
                urgency=UrgencyEnum.HIGH,
            ),
            business_impact="May affect renewal decision",
            confidence=0.92,
            themes=["pricing_sensitivity", "competitive_pressure"],
        )
        assert classification.category == CategoryEnum.COMPLAINT
        assert classification.subcategory == "pricing"
        assert classification.sentiment.polarity == PolarityEnum.NEGATIVE
        assert classification.business_impact == "May affect renewal decision"
        assert classification.confidence == 0.92
        assert len(classification.themes) == 2

    def test_creation_with_minimal_fields(self):
        classification = FeedbackClassification(
            category=CategoryEnum.QUESTION,
            sentiment=SentimentScore(
                polarity=PolarityEnum.NEUTRAL,
                intensity=0.5,
                urgency=UrgencyEnum.LOW,
            ),
            business_impact="Standard review required",
            confidence=0.5,
        )
        assert classification.category == CategoryEnum.QUESTION
        assert classification.subcategory is None
        assert classification.themes == []

    def test_confidence_at_boundaries(self):
        low = FeedbackClassification(
            category=CategoryEnum.BUG,
            sentiment=SentimentScore(polarity=PolarityEnum.NEUTRAL, intensity=0.5, urgency=UrgencyEnum.LOW),
            business_impact="Low",
            confidence=0.0,
        )
        assert low.confidence == 0.0

        high = FeedbackClassification(
            category=CategoryEnum.BUG,
            sentiment=SentimentScore(polarity=PolarityEnum.NEUTRAL, intensity=0.5, urgency=UrgencyEnum.LOW),
            business_impact="Low",
            confidence=1.0,
        )
        assert high.confidence == 1.0

    def test_confidence_out_of_range_raises_error(self):
        with pytest.raises(ValidationError):
            FeedbackClassification(
                category=CategoryEnum.BUG,
                sentiment=SentimentScore(polarity=PolarityEnum.NEUTRAL, intensity=0.5, urgency=UrgencyEnum.LOW),
                business_impact="Low",
                confidence=1.5,
            )

    def test_all_category_enum_values(self):
        for category in CategoryEnum:
            classification = FeedbackClassification(
                category=category,
                sentiment=SentimentScore(polarity=PolarityEnum.NEUTRAL, intensity=0.5, urgency=UrgencyEnum.LOW),
                business_impact="Standard",
                confidence=0.5,
            )
            assert classification.category == category

    def test_invalid_category_raises_error(self):
        with pytest.raises(ValidationError):
            FeedbackClassification(
                category="not_a_real_category",
                sentiment=SentimentScore(polarity=PolarityEnum.NEUTRAL, intensity=0.5, urgency=UrgencyEnum.LOW),
                business_impact="N/A",
                confidence=0.5,
            )


# ---------------------------------------------------------------------------
# FeedbackRouting tests
# ---------------------------------------------------------------------------

class TestFeedbackRouting:
    """Test FeedbackRouting model."""

    def test_creation_with_all_fields(self):
        routing = FeedbackRouting(
            action="route_to_sales",
            assigned_team="sales",
            assigned_individual="sarah_johnson",
            channel="email",
            escalated=True,
            escalation_reason="High-value prospect with competitive threat",
            recommended_action="Schedule call with pricing team",
        )
        assert routing.action == "route_to_sales"
        assert routing.assigned_team == "sales"
        assert routing.assigned_individual == "sarah_johnson"
        assert routing.channel == "email"
        assert routing.escalated is True
        assert routing.escalation_reason == "High-value prospect with competitive threat"

    def test_creation_with_minimal_fields(self):
        routing = FeedbackRouting(
            action="route_to_support",
            channel="email",
            recommended_action="Review and classify",
        )
        assert routing.action == "route_to_support"
        assert routing.assigned_team is None
        assert routing.assigned_individual is None
        assert routing.escalated is False  # default
        assert routing.escalation_reason is None

    def test_missing_required_fields_raises_error(self):
        with pytest.raises(ValidationError):
            FeedbackRouting(action="route_to_support")  # missing channel and recommended_action


# ---------------------------------------------------------------------------
# FeedbackResponse tests
# ---------------------------------------------------------------------------

class TestFeedbackResponse:
    """Test FeedbackResponse model."""

    def test_creation_with_all_fields(self):
        response = FeedbackResponse(
            auto_responded=True,
            response_text="Thank you for reaching out about pricing.",
            response_type=ResponseTypeEnum.AUTO_ACKNOWLEDGE,
        )
        assert response.auto_responded is True
        assert response.response_text == "Thank you for reaching out about pricing."
        assert response.response_type == ResponseTypeEnum.AUTO_ACKNOWLEDGE

    def test_creation_with_minimal_fields(self):
        response = FeedbackResponse(
            response_type=ResponseTypeEnum.FLAG_HUMAN,
        )
        assert response.auto_responded is False  # default
        assert response.response_text is None
        assert response.response_type == ResponseTypeEnum.FLAG_HUMAN

    def test_all_response_type_enum_values(self):
        for rtype in ResponseTypeEnum:
            response = FeedbackResponse(response_type=rtype)
            assert response.response_type == rtype

    def test_invalid_response_type_raises_error(self):
        with pytest.raises(ValidationError):
            FeedbackResponse(response_type="invalid_response_type")


# ---------------------------------------------------------------------------
# FeedbackLifecycle tests
# ---------------------------------------------------------------------------

class TestFeedbackLifecycle:
    """Test FeedbackLifecycle model."""

    def test_creation(self):
        lifecycle = FeedbackLifecycle(status=FeedbackStatusEnum.RECEIVED)
        assert lifecycle.status == FeedbackStatusEnum.RECEIVED
        assert lifecycle.loop_closed is False

    def test_all_status_values(self):
        for status in FeedbackStatusEnum:
            lifecycle = FeedbackLifecycle(status=status)
            assert lifecycle.status == status

    def test_loop_closed(self):
        lifecycle = FeedbackLifecycle(status=FeedbackStatusEnum.CLOSED, loop_closed=True)
        assert lifecycle.loop_closed is True


# ---------------------------------------------------------------------------
# FeedbackItem tests
# ---------------------------------------------------------------------------

class TestFeedbackItem:
    """Test FeedbackItem model (top-level composite)."""

    def test_creation_with_all_fields(self, sample_feedback_source, sample_feedback_contact,
                                      sample_feedback_content, sample_classification):
        item = FeedbackItem(
            id="fb_abc123def456",
            timestamp=datetime(2025, 1, 20, 14, 30, 0),
            source=sample_feedback_source,
            contact=sample_feedback_contact,
            content=sample_feedback_content,
            classification=sample_classification,
            routing=FeedbackRouting(
                action="route_to_sales",
                channel="email",
                recommended_action="Follow up",
            ),
            response=FeedbackResponse(response_type=ResponseTypeEnum.AUTO_ACKNOWLEDGE),
            lifecycle=FeedbackLifecycle(status=FeedbackStatusEnum.ROUTED),
        )
        assert item.id == "fb_abc123def456"
        assert item.source.channel == FeedbackSourceEnum.WEBSITE_FORM
        assert item.contact.type == ContactTypeEnum.PROSPECT
        assert item.content.raw_text is not None
        assert item.classification.category == CategoryEnum.FEATURE
        assert item.routing.action == "route_to_sales"
        assert item.response.response_type == ResponseTypeEnum.AUTO_ACKNOWLEDGE
        assert item.lifecycle.status == FeedbackStatusEnum.ROUTED

    def test_creation_with_minimal_fields(self, sample_feedback_source, sample_feedback_contact,
                                           sample_feedback_content):
        item = FeedbackItem(
            id="fb_minimal",
            source=sample_feedback_source,
            contact=sample_feedback_contact,
            content=sample_feedback_content,
        )
        assert item.id == "fb_minimal"
        assert item.classification is None
        assert item.routing is None
        assert item.response is None
        assert item.lifecycle.status == FeedbackStatusEnum.RECEIVED  # default

    def test_timestamp_defaults_to_now(self, sample_feedback_source, sample_feedback_contact,
                                        sample_feedback_content):
        item = FeedbackItem(
            id="fb_ts_test",
            source=sample_feedback_source,
            contact=sample_feedback_contact,
            content=sample_feedback_content,
        )
        assert item.timestamp is not None
        assert isinstance(item.timestamp, datetime)

    def test_missing_required_id_raises_error(self, sample_feedback_source, sample_feedback_contact,
                                               sample_feedback_content):
        with pytest.raises(ValidationError):
            FeedbackItem(
                source=sample_feedback_source,
                contact=sample_feedback_contact,
                content=sample_feedback_content,
            )


# ---------------------------------------------------------------------------
# ClassificationRequest / ClassificationOutput tests
# ---------------------------------------------------------------------------

class TestClassificationSchemas:
    """Test classification request/output schemas."""

    def test_classification_request(self):
        req = ClassificationRequest(
            text="This is broken and unusable!",
            context={"source": "website"},
        )
        assert req.text == "This is broken and unusable!"
        assert req.context == {"source": "website"}

    def test_classification_request_minimal(self):
        req = ClassificationRequest(text="feedback text")
        assert req.text == "feedback text"
        assert req.context == {}

    def test_classification_output(self):
        output = ClassificationOutput(
            category=CategoryEnum.BUG,
            subcategory="ui",
            sentiment=SentimentScore(
                polarity=PolarityEnum.NEGATIVE,
                intensity=0.8,
                urgency=UrgencyEnum.HIGH,
            ),
            business_impact="May impact renewal decision",
            confidence=0.95,
            themes=["implementation_friction"],
            reasoning="Customer explicitly reported a bug with UI",
        )
        assert output.category == CategoryEnum.BUG
        assert output.confidence == 0.95
        assert output.reasoning == "Customer explicitly reported a bug with UI"

    def test_classification_output_requires_reasoning(self):
        with pytest.raises(ValidationError):
            ClassificationOutput(
                category=CategoryEnum.BUG,
                sentiment=SentimentScore(polarity=PolarityEnum.NEUTRAL, intensity=0.5, urgency=UrgencyEnum.LOW),
                business_impact="Low",
                confidence=0.5,
                # missing reasoning
            )


# ---------------------------------------------------------------------------
# RoutingDecision tests
# ---------------------------------------------------------------------------

class TestRoutingDecisionSchema:
    """Test RoutingDecision schema model."""

    def test_creation_with_all_fields(self):
        decision = RoutingDecision(
            action="route_to_sales",
            assigned_team="sales",
            assigned_individual="sales_rep_001",
            channel="email",
            escalated=True,
            escalation_reason="High-value prospect",
            escalation_trigger="sentiment_intensity_high",
            recommended_action="Schedule call",
            response_type="auto_acknowledge",
            priority=1,
            rules_applied=["high_value_prospect_escalation"],
        )
        assert decision.action == "route_to_sales"
        assert decision.escalated is True
        assert decision.priority == 1
        assert len(decision.rules_applied) == 1

    def test_creation_with_defaults(self):
        decision = RoutingDecision(
            action="route_to_support",
            channel="email",
            recommended_action="Review",
            response_type="flag_human",
        )
        assert decision.escalated is False
        assert decision.priority == 3
        assert decision.rules_applied == []
        assert decision.escalation_reason is None
        assert decision.escalation_trigger is None


# ---------------------------------------------------------------------------
# ResponseOutput tests
# ---------------------------------------------------------------------------

class TestResponseOutputSchema:
    """Test ResponseOutput schema model."""

    def test_creation_with_all_fields(self):
        output = ResponseOutput(
            response_text="Thank you for your feedback.",
            response_type=ResponseTypeEnum.AUTO_ACKNOWLEDGE,
            should_auto_send=True,
            requires_human_review=False,
            tone="warm_and_professional",
        )
        assert output.response_text == "Thank you for your feedback."
        assert output.should_auto_send is True
        assert output.requires_human_review is False
        assert output.tone == "warm_and_professional"

    def test_creation_with_minimal_fields(self):
        output = ResponseOutput(
            response_text="Pending review",
            response_type=ResponseTypeEnum.FLAG_HUMAN,
            tone="professional",
        )
        assert output.should_auto_send is False  # default
        assert output.requires_human_review is False  # default

    def test_missing_required_fields_raises_error(self):
        with pytest.raises(ValidationError):
            ResponseOutput(
                response_text="Text only",
                # missing response_type and tone
            )
