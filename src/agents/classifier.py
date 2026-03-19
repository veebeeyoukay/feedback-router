"""Classifier agent for analyzing feedback."""

from typing import Optional
import json
from src.schemas.feedback import (
    FeedbackItem, FeedbackClassification, CategoryEnum, SentimentScore,
    PolarityEnum, UrgencyEnum
)
from src.schemas.classification import ClassificationOutput
from src.classification.categories import get_category_definition
from src.classification.sentiment import analyze_sentiment
from src.classification.themes import tag_themes


class ClassifierAgent:
    """Classifies feedback using LLM with fallback to rules."""

    def __init__(self, llm_client: Optional[object] = None, use_llm: bool = True):
        """Initialize classifier agent.

        Args:
            llm_client: Optional LLM client (e.g., Anthropic)
            use_llm: Whether to attempt LLM classification
        """
        self.llm_client = llm_client
        self.use_llm = use_llm

    def classify(self, feedback_item: FeedbackItem) -> FeedbackClassification:
        """Classify feedback item.

        Args:
            feedback_item: Feedback item to classify

        Returns:
            Classification results
        """
        # Try LLM classification if available
        if self.use_llm and self.llm_client:
            try:
                classification = self._classify_with_llm(feedback_item)
                if classification:
                    return classification
            except Exception:
                pass

        # Fall back to rule-based classification
        return self._classify_with_rules(feedback_item)

    def _classify_with_llm(self, feedback_item: FeedbackItem) -> Optional[FeedbackClassification]:
        """Classify using LLM.

        Args:
            feedback_item: Feedback item to classify

        Returns:
            Classification or None if unavailable
        """
        # This would call Claude API with structured output
        # For now, returns None to trigger fallback
        # Implementation would use anthropic client
        return None

    def _classify_with_rules(self, feedback_item: FeedbackItem) -> FeedbackClassification:
        """Classify using rule-based approach.

        Args:
            feedback_item: Feedback item to classify

        Returns:
            Classification results
        """
        text = feedback_item.content.raw_text
        text_lower = text.lower()

        # Sentiment analysis
        polarity, intensity, urgency = analyze_sentiment(text)

        # Category detection
        category = self._detect_category(text_lower)

        # Theme detection
        themes = tag_themes(text)

        # Business impact assessment
        business_impact = self._assess_business_impact(
            category,
            intensity,
            feedback_item.contact.type.value,
            urgency
        )

        # Confidence score (based on text length and category clarity)
        confidence = self._calculate_confidence(text_lower, category, intensity)

        return FeedbackClassification(
            category=category,
            subcategory=None,
            sentiment=SentimentScore(
                polarity=polarity,
                intensity=intensity,
                urgency=urgency
            ),
            business_impact=business_impact,
            confidence=confidence,
            themes=themes
        )

    def _detect_category(self, text_lower: str) -> CategoryEnum:
        """Detect primary category from text.

        Args:
            text_lower: Lowercased feedback text

        Returns:
            CategoryEnum for primary category
        """
        # Check each category's keywords
        category_scores = {}

        for category in CategoryEnum:
            definition = get_category_definition(category)
            keyword_matches = sum(
                1 for keyword in definition.keywords
                if keyword in text_lower
            )
            category_scores[category] = keyword_matches

        # Return category with highest score, default to "question"
        if max(category_scores.values()) > 0:
            return max(category_scores, key=category_scores.get)
        return CategoryEnum.QUESTION

    def _assess_business_impact(self, category: CategoryEnum, intensity: float,
                               contact_type: str, urgency: str) -> str:
        """Assess business impact.

        Args:
            category: Feedback category
            intensity: Sentiment intensity
            contact_type: Type of contact
            urgency: Urgency level

        Returns:
            Business impact description
        """
        impacts = []

        # Impact based on contact type
        if contact_type == "client":
            impacts.append("Client satisfaction at risk")
        elif contact_type == "churned":
            impacts.append("Churn risk - lost revenue")
        elif contact_type == "prospect":
            if intensity > 0.7:
                impacts.append("Deal at risk")

        # Impact based on category
        if category == CategoryEnum.BUG:
            impacts.append("Product quality issue")
        elif category == CategoryEnum.COMPLAINT:
            impacts.append("Customer dissatisfaction")
        elif category == CategoryEnum.LOST:
            impacts.append("Potential churn")

        # Impact based on urgency
        if urgency == UrgencyEnum.CRITICAL:
            impacts.append("Immediate action required")
        elif urgency == UrgencyEnum.HIGH:
            impacts.append("High priority issue")

        return " - ".join(impacts) if impacts else "Standard review required"

    def _calculate_confidence(self, text_lower: str, category: CategoryEnum,
                             intensity: float) -> float:
        """Calculate classification confidence.

        Args:
            text_lower: Lowercased text
            category: Detected category
            intensity: Sentiment intensity

        Returns:
            Confidence score 0-1
        """
        confidence = 0.5

        # Higher confidence with longer, clearer feedback
        text_length = len(text_lower.split())
        if text_length > 50:
            confidence += 0.2
        elif text_length > 20:
            confidence += 0.1

        # Higher confidence if clear sentiment
        if intensity > 0.7 or intensity < 0.3:
            confidence += 0.15

        # Higher confidence with category keywords
        definition = get_category_definition(category)
        keyword_matches = sum(
            1 for keyword in definition.keywords
            if keyword in text_lower
        )
        if keyword_matches >= 2:
            confidence += 0.15
        elif keyword_matches == 1:
            confidence += 0.05

        return min(confidence, 0.99)
