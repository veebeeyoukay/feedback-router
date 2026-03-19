"""Unified feedback schema with Pydantic v2."""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class FeedbackSourceEnum(str, Enum):
    """Feedback source channels."""
    WEBSITE_FORM = "website_form"
    WEBSITE_CHAT = "website_chat"
    WEBSITE_404 = "website_404"
    SLACK = "slack"
    EMAIL = "email"
    TWITTER = "twitter"
    INTERCOM = "intercom"


class FeedbackSource(BaseModel):
    """Source information about the feedback."""
    channel: FeedbackSourceEnum = Field(..., description="Channel feedback came from")
    platform: Optional[str] = Field(None, description="Platform identifier")
    raw_id: str = Field(..., description="Original ID from source system")
    context: Optional[dict] = Field(default_factory=dict, description="Channel-specific context")

    model_config = {"json_schema_extra": {
        "example": {
            "channel": "website_form",
            "platform": "contact_form_v1",
            "raw_id": "form_12345",
            "context": {"page_url": "https://example.com/pricing"}
        }
    }}


class ContactTypeEnum(str, Enum):
    """Contact type classification."""
    PROSPECT = "prospect"
    CLIENT = "client"
    CHURNED = "churned"
    INTERNAL = "internal"
    UNKNOWN = "unknown"


class FeedbackContact(BaseModel):
    """Contact information associated with feedback."""
    type: ContactTypeEnum = Field(..., description="Contact type")
    id: Optional[str] = Field(None, description="Contact ID in our system")
    name: Optional[str] = Field(None, description="Contact name")
    account: Optional[str] = Field(None, description="Account ID if client")
    history: Optional[dict] = Field(default_factory=dict, description="Contact interaction history")

    model_config = {"json_schema_extra": {
        "example": {
            "type": "prospect",
            "id": "cont_123",
            "name": "John Doe",
            "account": None,
            "history": {"previous_inquiries": 2, "first_contact": "2025-01-15"}
        }
    }}


class FeedbackContent(BaseModel):
    """The actual feedback content."""
    raw_text: str = Field(..., description="Original feedback text")
    summary: Optional[str] = Field(None, description="Auto-generated summary")
    language: str = Field(default="en", description="Detected language code")

    model_config = {"json_schema_extra": {
        "example": {
            "raw_text": "Your pricing is too high compared to competitors",
            "summary": "Customer concerned about pricing competitiveness",
            "language": "en"
        }
    }}


class PolarityEnum(str, Enum):
    """Sentiment polarity."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class UrgencyEnum(str, Enum):
    """Urgency levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SentimentScore(BaseModel):
    """Sentiment analysis results."""
    polarity: PolarityEnum = Field(..., description="Sentiment polarity")
    intensity: float = Field(..., ge=0.0, le=1.0, description="Intensity score 0-1")
    urgency: UrgencyEnum = Field(..., description="Urgency level")

    model_config = {"json_schema_extra": {
        "example": {
            "polarity": "negative",
            "intensity": 0.85,
            "urgency": "high"
        }
    }}


class CategoryEnum(str, Enum):
    """Feedback categories."""
    BUG = "bug"
    FEATURE = "feature"
    QUESTION = "question"
    COMPLAINT = "complaint"
    PRAISE = "praise"
    SUGGESTION = "suggestion"
    LOST = "lost"
    ESCALATION = "escalation"


class FeedbackClassification(BaseModel):
    """Classification results for feedback."""
    category: CategoryEnum = Field(..., description="Primary category")
    subcategory: Optional[str] = Field(None, description="Subcategory within category")
    sentiment: SentimentScore = Field(..., description="Sentiment analysis")
    business_impact: str = Field(..., description="Expected business impact")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    themes: List[str] = Field(default_factory=list, description="ICP themes detected")

    model_config = {"json_schema_extra": {
        "example": {
            "category": "complaint",
            "subcategory": "pricing",
            "sentiment": {
                "polarity": "negative",
                "intensity": 0.75,
                "urgency": "high"
            },
            "business_impact": "May affect renewal decision",
            "confidence": 0.92,
            "themes": ["pricing_sensitivity", "competitive_pressure"]
        }
    }}


class FeedbackRouting(BaseModel):
    """Routing and assignment decision."""
    action: str = Field(..., description="Action to take")
    assigned_team: Optional[str] = Field(None, description="Team assignment")
    assigned_individual: Optional[str] = Field(None, description="Individual assignee")
    channel: str = Field(..., description="Response channel")
    escalated: bool = Field(default=False, description="Whether escalated")
    escalation_reason: Optional[str] = Field(None, description="Reason for escalation if escalated")
    recommended_action: str = Field(..., description="Recommended next action")

    model_config = {"json_schema_extra": {
        "example": {
            "action": "route_to_sales",
            "assigned_team": "sales",
            "assigned_individual": "sarah_johnson",
            "channel": "email",
            "escalated": True,
            "escalation_reason": "High-value prospect with competitive threat",
            "recommended_action": "Schedule call with pricing team"
        }
    }}


class ResponseTypeEnum(str, Enum):
    """Response type classification."""
    AUTO_ACKNOWLEDGE = "auto_acknowledge"
    DRAFT_FAQ = "draft_faq"
    DRAFT_COMPLEX = "draft_complex"
    FLAG_HUMAN = "flag_human"


class FeedbackResponse(BaseModel):
    """Response generated for feedback."""
    auto_responded: bool = Field(default=False, description="Whether auto-response sent")
    response_text: Optional[str] = Field(None, description="Generated response text")
    response_type: ResponseTypeEnum = Field(..., description="Type of response")

    model_config = {"json_schema_extra": {
        "example": {
            "auto_responded": True,
            "response_text": "Thank you for reaching out about pricing. Our sales team will contact you shortly.",
            "response_type": "auto_acknowledge"
        }
    }}


class FeedbackStatusEnum(str, Enum):
    """Feedback status in lifecycle."""
    RECEIVED = "received"
    CLASSIFIED = "classified"
    ROUTED = "routed"
    RESPONDED = "responded"
    RESOLVED = "resolved"
    CLOSED = "closed"


class FeedbackLifecycle(BaseModel):
    """Lifecycle tracking."""
    status: FeedbackStatusEnum = Field(..., description="Current status")
    loop_closed: bool = Field(default=False, description="Whether feedback loop is closed")

    model_config = {"json_schema_extra": {
        "example": {
            "status": "routed",
            "loop_closed": False
        }
    }}


class FeedbackItem(BaseModel):
    """Complete unified feedback item."""
    id: str = Field(..., description="Unique feedback ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When feedback was received")
    source: FeedbackSource = Field(..., description="Source information")
    contact: FeedbackContact = Field(..., description="Contact information")
    content: FeedbackContent = Field(..., description="Feedback content")
    classification: Optional[FeedbackClassification] = Field(None, description="Classification results")
    routing: Optional[FeedbackRouting] = Field(None, description="Routing decision")
    response: Optional[FeedbackResponse] = Field(None, description="Generated response")
    lifecycle: FeedbackLifecycle = Field(default_factory=lambda: FeedbackLifecycle(status="received"),
                                         description="Lifecycle tracking")

    model_config = {"json_schema_extra": {
        "example": {
            "id": "fb_abc123def456",
            "timestamp": "2025-01-20T14:30:00Z",
            "source": {
                "channel": "website_form",
                "platform": "contact_form_v1",
                "raw_id": "form_12345",
                "context": {"page_url": "https://example.com/pricing"}
            },
            "contact": {
                "type": "prospect",
                "id": "cont_123",
                "name": "John Doe",
                "account": None,
                "history": {"previous_inquiries": 2}
            },
            "content": {
                "raw_text": "Your pricing is too high",
                "summary": "Customer concerned about pricing",
                "language": "en"
            },
            "classification": {
                "category": "complaint",
                "subcategory": "pricing",
                "sentiment": {
                    "polarity": "negative",
                    "intensity": 0.75,
                    "urgency": "high"
                },
                "business_impact": "May affect renewal",
                "confidence": 0.92,
                "themes": ["pricing_sensitivity"]
            },
            "routing": {
                "action": "route_to_sales",
                "assigned_team": "sales",
                "assigned_individual": "sarah_johnson",
                "channel": "email",
                "escalated": True,
                "escalation_reason": "High-value prospect",
                "recommended_action": "Schedule call"
            },
            "response": {
                "auto_responded": True,
                "response_text": "Thank you for contacting us...",
                "response_type": "auto_acknowledge"
            },
            "lifecycle": {
                "status": "routed",
                "loop_closed": False
            }
        }
    }}
