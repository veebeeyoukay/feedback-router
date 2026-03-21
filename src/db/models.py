"""SQLAlchemy ORM models for the feedback router database."""

from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    String,
    Text,
    Float,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class FeedbackRecord(Base):
    """Persisted feedback item.

    Maps to the FeedbackItem Pydantic schema. Stores the core feedback
    data including source, contact, and content information.
    """

    __tablename__ = "feedback_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Source fields (flattened from FeedbackSource)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    source_platform: Mapped[Optional[str]] = mapped_column(String(100))
    source_raw_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_context: Mapped[Optional[dict]] = mapped_column(JSON)

    # Contact fields (flattened from FeedbackContact)
    contact_type: Mapped[str] = mapped_column(String(50), nullable=False)
    contact_id: Mapped[Optional[str]] = mapped_column(String(255))
    contact_name: Mapped[Optional[str]] = mapped_column(String(255))
    contact_email: Mapped[Optional[str]] = mapped_column(String(255))
    contact_account: Mapped[Optional[str]] = mapped_column(String(255))

    # Content fields (flattened from FeedbackContent)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(10), default="en")

    # Lifecycle
    status: Mapped[str] = mapped_column(String(50), default="received")
    loop_closed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    classification: Mapped[Optional["ClassificationRecord"]] = relationship(
        back_populates="feedback",
        uselist=False,
        cascade="all, delete-orphan",
    )
    routing: Mapped[Optional["RoutingRecord"]] = relationship(
        back_populates="feedback",
        uselist=False,
        cascade="all, delete-orphan",
    )
    response: Mapped[Optional["ResponseRecord"]] = relationship(
        back_populates="feedback",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<FeedbackRecord id={self.id} channel={self.channel} status={self.status}>"


class ClassificationRecord(Base):
    """Persisted classification result.

    Maps to the FeedbackClassification Pydantic schema. Stores category,
    sentiment analysis, and theme data for a feedback item.
    """

    __tablename__ = "classification_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feedback_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("feedback_records.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    category: Mapped[str] = mapped_column(String(50), nullable=False)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100))

    # Sentiment fields (flattened from SentimentScore)
    polarity: Mapped[str] = mapped_column(String(20), nullable=False)
    intensity: Mapped[float] = mapped_column(Float, nullable=False)
    urgency: Mapped[str] = mapped_column(String(20), nullable=False)

    business_impact: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    themes: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationship
    feedback: Mapped["FeedbackRecord"] = relationship(
        back_populates="classification",
    )

    def __repr__(self) -> str:
        return (
            f"<ClassificationRecord feedback_id={self.feedback_id} "
            f"category={self.category} confidence={self.confidence}>"
        )


class RoutingRecord(Base):
    """Persisted routing decision.

    Maps to the RoutingDecision Pydantic schema. Stores the action taken,
    team assignment, escalation info, and applied rules.
    """

    __tablename__ = "routing_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feedback_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("feedback_records.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    action: Mapped[str] = mapped_column(String(100), nullable=False)
    assigned_team: Mapped[Optional[str]] = mapped_column(String(100))
    assigned_individual: Mapped[Optional[str]] = mapped_column(String(255))
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    escalation_reason: Mapped[Optional[str]] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, default=3)
    response_type: Mapped[Optional[str]] = mapped_column(String(50))
    rules_applied: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationship
    feedback: Mapped["FeedbackRecord"] = relationship(
        back_populates="routing",
    )

    def __repr__(self) -> str:
        return (
            f"<RoutingRecord feedback_id={self.feedback_id} "
            f"action={self.action} escalated={self.escalated}>"
        )


class ResponseRecord(Base):
    """Persisted response generated for feedback.

    Maps to the FeedbackResponse Pydantic schema. Stores the response
    text, type, and whether it was automatically sent.
    """

    __tablename__ = "response_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feedback_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("feedback_records.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    auto_responded: Mapped[bool] = mapped_column(Boolean, default=False)
    response_text: Mapped[Optional[str]] = mapped_column(Text)
    response_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationship
    feedback: Mapped["FeedbackRecord"] = relationship(
        back_populates="response",
    )

    def __repr__(self) -> str:
        return (
            f"<ResponseRecord feedback_id={self.feedback_id} "
            f"response_type={self.response_type} auto={self.auto_responded}>"
        )
