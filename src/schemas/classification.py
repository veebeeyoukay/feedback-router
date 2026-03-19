"""Classification schema models."""

from pydantic import BaseModel, Field
from typing import Optional, List
from src.schemas.feedback import CategoryEnum, PolarityEnum, UrgencyEnum, SentimentScore


class ClassificationRequest(BaseModel):
    """Request for classification of feedback."""
    text: str = Field(..., description="Feedback text to classify")
    context: Optional[dict] = Field(default_factory=dict, description="Additional context")


class ClassificationOutput(BaseModel):
    """Output from classification process."""
    category: CategoryEnum = Field(..., description="Primary category")
    subcategory: Optional[str] = Field(None, description="Subcategory")
    sentiment: SentimentScore = Field(..., description="Sentiment analysis")
    business_impact: str = Field(..., description="Expected business impact")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    themes: List[str] = Field(default_factory=list, description="Detected themes")
    reasoning: str = Field(..., description="Explanation of classification")

    model_config = {"json_schema_extra": {
        "example": {
            "category": "complaint",
            "subcategory": "pricing",
            "sentiment": {
                "polarity": "negative",
                "intensity": 0.8,
                "urgency": "high"
            },
            "business_impact": "May impact renewal decision",
            "confidence": 0.95,
            "themes": ["pricing_sensitivity", "competitive_pressure"],
            "reasoning": "Customer explicitly expressed concern about pricing relative to competitors"
        }
    }}
