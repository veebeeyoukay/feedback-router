"""Feedback category taxonomy."""

from enum import Enum
from dataclasses import dataclass
from typing import List


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


@dataclass
class CategoryDefinition:
    """Definition of a feedback category."""
    name: str
    description: str
    examples: List[str]
    keywords: List[str]


CATEGORY_DEFINITIONS = {
    CategoryEnum.BUG: CategoryDefinition(
        name="Bug",
        description="Technical issues, errors, crashes, or unexpected behavior",
        examples=[
            "The dashboard won't load after I updated",
            "Getting a 500 error when uploading files",
            "The export button doesn't work"
        ],
        keywords=["bug", "error", "crash", "broken", "not working", "exception", "failed", "issue", "problem"]
    ),
    CategoryEnum.FEATURE: CategoryDefinition(
        name="Feature Request",
        description="Requests for new functionality or product enhancements",
        examples=[
            "We need dark mode support",
            "Can you add bulk export capability?",
            "Would love to see API webhooks"
        ],
        keywords=["feature", "request", "add", "implement", "need", "want", "enhancement", "capability", "function"]
    ),
    CategoryEnum.QUESTION: CategoryDefinition(
        name="Question",
        description="How-to questions, usage clarification, documentation",
        examples=[
            "How do I reset my password?",
            "What's the API rate limit?",
            "How do I integrate with Slack?"
        ],
        keywords=["how", "what", "can", "help", "question", "help me", "confused", "understand", "explain"]
    ),
    CategoryEnum.COMPLAINT: CategoryDefinition(
        name="Complaint",
        description="Dissatisfaction with product, pricing, service, or support",
        examples=[
            "Your pricing is too high",
            "Customer support takes too long to respond",
            "The UI is confusing and hard to use"
        ],
        keywords=["complaint", "frustrated", "disappointed", "unhappy", "dissatisfied", "poor", "bad", "terrible"]
    ),
    CategoryEnum.PRAISE: CategoryDefinition(
        name="Praise",
        description="Positive feedback, compliments, and appreciation",
        examples=[
            "Love the new dashboard redesign!",
            "Your customer service is amazing",
            "Best tool we've used for this"
        ],
        keywords=["great", "love", "awesome", "excellent", "amazing", "impressed", "fantastic", "perfect", "best"]
    ),
    CategoryEnum.SUGGESTION: CategoryDefinition(
        name="Suggestion",
        description="Ideas and recommendations for improvement",
        examples=[
            "You should add a dark mode",
            "Consider improving the onboarding process",
            "Maybe add keyboard shortcuts?"
        ],
        keywords=["suggest", "recommendation", "consider", "maybe", "could", "should", "idea", "think"]
    ),
    CategoryEnum.LOST: CategoryDefinition(
        name="Lost/Churn Risk",
        description="Customer indicating they may leave or use competitors",
        examples=[
            "We're considering switching to Competitor X",
            "Looking at alternatives because of pricing",
            "Not sure if this is the right fit for us"
        ],
        keywords=["cancel", "switching", "competitor", "alternative", "leave", "churn", "replace", "migrate"]
    ),
    CategoryEnum.ESCALATION: CategoryDefinition(
        name="Escalation",
        description="Issues that require immediate attention or high-level intervention",
        examples=[
            "Executive sponsor concerned about roadmap",
            "Security vulnerability found",
            "Major account at risk"
        ],
        keywords=["urgent", "critical", "escalate", "executive", "security", "compliance", "breach"]
    ),
}


def get_category_definition(category: CategoryEnum) -> CategoryDefinition:
    """Get the definition for a category.

    Args:
        category: The category enum value

    Returns:
        CategoryDefinition with metadata
    """
    return CATEGORY_DEFINITIONS[category]


def get_all_categories() -> dict:
    """Get all category definitions.

    Returns:
        Dictionary of all categories and their definitions
    """
    return CATEGORY_DEFINITIONS
