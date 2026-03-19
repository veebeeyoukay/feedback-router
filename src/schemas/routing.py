"""Routing decision schema models."""

from pydantic import BaseModel, Field
from typing import Optional, List
from src.schemas.feedback import FeedbackClassification, ResponseTypeEnum


class RoutingRequest(BaseModel):
    """Request for routing decision."""
    classification: FeedbackClassification = Field(..., description="Classification results")
    context: Optional[dict] = Field(default_factory=dict, description="Additional context")


class RoutingDecision(BaseModel):
    """Routing decision output."""
    action: str = Field(..., description="Action to take")
    assigned_team: Optional[str] = Field(None, description="Team assignment")
    assigned_individual: Optional[str] = Field(None, description="Individual assignee")
    channel: str = Field(..., description="Preferred response channel")
    escalated: bool = Field(default=False, description="Whether escalated")
    escalation_reason: Optional[str] = Field(None, description="Escalation reason if applicable")
    escalation_trigger: Optional[str] = Field(None, description="What triggered escalation")
    recommended_action: str = Field(..., description="Recommended next step")
    response_type: ResponseTypeEnum = Field(..., description="Type of response to generate")
    priority: int = Field(default=3, description="Priority 1-5, lower is higher priority")
    rules_applied: List[str] = Field(default_factory=list, description="Rules that matched")

    model_config = {"json_schema_extra": {
        "example": {
            "action": "route_to_sales",
            "assigned_team": "sales",
            "assigned_individual": "sales_rep_001",
            "channel": "email",
            "escalated": True,
            "escalation_reason": "High-value prospect with competitive threat",
            "escalation_trigger": "sentiment_intensity_high_and_negative",
            "recommended_action": "Schedule call with pricing team",
            "response_type": "auto_acknowledge",
            "priority": 1,
            "rules_applied": ["high_value_prospect", "negative_sentiment_escalation"]
        }
    }}
