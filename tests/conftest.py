"""Shared pytest fixtures for feedback router tests."""

import pytest
from datetime import datetime

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
from src.schemas.routing import RoutingDecision


@pytest.fixture
def sample_feedback_source():
    """Create a sample FeedbackSource."""
    return FeedbackSource(
        channel=FeedbackSourceEnum.WEBSITE_FORM,
        platform="contact_form_v1",
        raw_id="form_12345",
        context={"page_url": "https://example.com/pricing"},
    )


@pytest.fixture
def sample_feedback_contact():
    """Create a sample FeedbackContact."""
    return FeedbackContact(
        type=ContactTypeEnum.PROSPECT,
        id="cont_123",
        name="Karen M.",
        account=None,
        history={"previous_inquiries": 0},
    )


@pytest.fixture
def sample_feedback_content():
    """Create a sample FeedbackContent."""
    return FeedbackContent(
        raw_text="We need a productivity tool that integrates with our workflow. Budget approved, deadline is Thursday.",
        summary="Prospect requesting productivity tool with urgent deadline",
        language="en",
    )


@pytest.fixture
def sample_sentiment_score():
    """Create a sample SentimentScore."""
    return SentimentScore(
        polarity=PolarityEnum.POSITIVE,
        intensity=0.65,
        urgency=UrgencyEnum.HIGH,
    )


@pytest.fixture
def sample_classification(sample_sentiment_score):
    """Create a sample FeedbackClassification."""
    return FeedbackClassification(
        category=CategoryEnum.FEATURE,
        subcategory="productivity",
        sentiment=sample_sentiment_score,
        business_impact="Deal at risk - High priority issue",
        confidence=0.85,
        themes=["pricing_sensitivity", "implementation_friction"],
    )


@pytest.fixture
def sample_feedback_item(sample_feedback_source, sample_feedback_contact, sample_feedback_content):
    """Create a sample FeedbackItem without classification."""
    return FeedbackItem(
        id="fb_test12345678",
        timestamp=datetime(2025, 1, 20, 14, 30, 0),
        source=sample_feedback_source,
        contact=sample_feedback_contact,
        content=sample_feedback_content,
        classification=None,
        routing=None,
        response=None,
        lifecycle=FeedbackLifecycle(status=FeedbackStatusEnum.RECEIVED),
    )


@pytest.fixture
def sample_classified_feedback_item(sample_feedback_item, sample_classification):
    """Create a sample FeedbackItem with classification attached."""
    sample_feedback_item.classification = sample_classification
    return sample_feedback_item


@pytest.fixture
def sample_routing_decision():
    """Create a sample RoutingDecision."""
    return RoutingDecision(
        action="route_to_sales",
        assigned_team="sales",
        assigned_individual="sales_rep_001",
        channel="email",
        escalated=True,
        escalation_reason="High-value prospect with competitive threat",
        escalation_trigger="sentiment_intensity_high",
        recommended_action="Schedule call with pricing team",
        response_type="auto_acknowledge",
        priority=1,
        rules_applied=["high_value_prospect_escalation"],
    )


@pytest.fixture
def sample_raw_feedback():
    """Create a sample raw feedback dictionary (as received from a channel)."""
    return {
        "id": "form_99999",
        "platform": "website_form",
        "text": "Your pricing is too high compared to competitors. We are considering switching.",
        "name": "Jane Smith",
        "email": "jane.smith@acme.com",
        "context": {"page_url": "https://example.com/pricing"},
    }


@pytest.fixture
def sample_raw_website_form():
    """Create a sample raw website form submission."""
    return {
        "id": "form_001",
        "name": "John Doe",
        "email": "john@example.com",
        "message": "I have a question about your enterprise plan pricing.",
        "page_url": "https://example.com/pricing",
        "ip_address": "192.168.1.1",
        "timestamp": "2025-01-20T14:30:00Z",
    }


@pytest.fixture
def sample_raw_slack_message():
    """Create a sample raw Slack message."""
    return {
        "ts": "1705757400.000100",
        "text": "Having trouble with the dashboard. It keeps crashing when I try to export.",
        "user": "U12345ABC",
        "channel": "feedback",
        "thread_ts": None,
        "reactions": [],
    }


@pytest.fixture
def sample_raw_email():
    """Create a sample raw email input."""
    return {
        "message_id": "msg_abc123",
        "from_name": "Alice Johnson",
        "from_email": "alice@bigcorp.com",
        "subject": "Feature Request: Dark Mode",
        "body": "We would love to see dark mode added. Our team works late hours and it would really help.",
        "date": "2025-01-20T18:00:00Z",
    }
