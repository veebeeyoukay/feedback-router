"""Response generation schema models."""

from pydantic import BaseModel, Field
from typing import Optional
from src.schemas.feedback import ResponseTypeEnum


class ResponseRequest(BaseModel):
    """Request for response generation."""
    feedback_text: str = Field(..., description="Original feedback text")
    category: str = Field(..., description="Feedback category")
    contact_type: str = Field(..., description="Contact type")
    context: Optional[dict] = Field(default_factory=dict, description="Additional context")


class ResponseOutput(BaseModel):
    """Generated response output."""
    response_text: str = Field(..., description="Generated response text")
    response_type: ResponseTypeEnum = Field(..., description="Type of response")
    should_auto_send: bool = Field(default=False, description="Whether to auto-send this response")
    requires_human_review: bool = Field(default=False, description="Whether human should review")
    tone: str = Field(..., description="Tone of response (warm, professional, empathetic, etc.)")

    model_config = {"json_schema_extra": {
        "example": {
            "response_text": "Thank you for sharing your feedback about pricing. We appreciate your interest and would love to discuss how our solution provides value. Our sales team will reach out shortly to explore options.",
            "response_type": "auto_acknowledge",
            "should_auto_send": True,
            "requires_human_review": False,
            "tone": "warm_and_professional"
        }
    }}
