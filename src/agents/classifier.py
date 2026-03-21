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

    def __init__(self, llm_client=None, use_llm: bool = True):
        """Initialize classifier agent.

        Args:
            llm_client: Optional LLM client (e.g., Anthropic)
            use_llm: Whether to attempt LLM classification
        """
        self.use_llm = use_llm
        if use_llm and llm_client is None:
            try:
                import anthropic
                self.llm_client = anthropic.Anthropic()
            except Exception:
                self.llm_client = None
                self.use_llm = False
        else:
            self.llm_client = llm_client

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
        try:
            prompt = (
                "You are a feedback classification system. Analyze the following customer feedback "
                "and return a JSON object with these fields:\n"
                "\n"
                "- category: one of: bug, feature, question, complaint, praise, suggestion, lost, escalation\n"
                "- sentiment_polarity: one of: positive, negative, neutral, mixed\n"
                "- sentiment_intensity: float between 0 and 1\n"
                "- urgency: one of: low, medium, high, critical\n"
                "- business_impact: a short text description of the business impact\n"
                "- themes: a list of relevant theme strings\n"
                "- confidence: float between 0 and 1 indicating your classification confidence\n"
                "\n"
                "Return ONLY valid JSON, no other text.\n"
                "\n"
                f"Feedback text: {feedback_item.content.raw_text}"
            )

            message = self.llm_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract text content from the response
            response_text = message.content[0].text

            # Parse JSON from the response, handling possible markdown code blocks
            response_text = response_text.strip()
            if response_text.startswith("```"):
                # Remove markdown code block wrapping
                lines = response_text.split("\n")
                # Drop first line (```json or ```) and last line (```)
                lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                response_text = "\n".join(lines)

            result = json.loads(response_text)

            # Map the response to a FeedbackClassification
            polarity_map = {
                "positive": PolarityEnum.POSITIVE,
                "negative": PolarityEnum.NEGATIVE,
                "neutral": PolarityEnum.NEUTRAL,
                "mixed": PolarityEnum.MIXED,
            }
            urgency_map = {
                "low": UrgencyEnum.LOW,
                "medium": UrgencyEnum.MEDIUM,
                "high": UrgencyEnum.HIGH,
                "critical": UrgencyEnum.CRITICAL,
            }
            category_map = {
                "bug": CategoryEnum.BUG,
                "feature": CategoryEnum.FEATURE,
                "question": CategoryEnum.QUESTION,
                "complaint": CategoryEnum.COMPLAINT,
                "praise": CategoryEnum.PRAISE,
                "suggestion": CategoryEnum.SUGGESTION,
                "lost": CategoryEnum.LOST,
                "escalation": CategoryEnum.ESCALATION,
            }

            category = category_map.get(result["category"], CategoryEnum.QUESTION)
            polarity = polarity_map.get(result["sentiment_polarity"], PolarityEnum.NEUTRAL)
            urgency = urgency_map.get(result["urgency"], UrgencyEnum.LOW)
            intensity = max(0.0, min(1.0, float(result["sentiment_intensity"])))
            confidence = max(0.0, min(1.0, float(result["confidence"])))
            business_impact = str(result.get("business_impact", "Standard review required"))
            themes = result.get("themes", [])
            if not isinstance(themes, list):
                themes = []

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
        except Exception:
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
