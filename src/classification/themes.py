"""ICP theme classification for feedback."""

from enum import Enum
from dataclasses import dataclass
from typing import List, Set
import re


class ThemeEnum(str, Enum):
    """ICP themes."""
    PRICING_SENSITIVITY = "pricing_sensitivity"
    COMPETITIVE_PRESSURE = "competitive_pressure"
    FEATURE_PARITY = "feature_parity"
    IMPLEMENTATION_FRICTION = "implementation_friction"
    SUPPORT_EXPECTATIONS = "support_expectations"


@dataclass
class ThemeDefinition:
    """Definition of an ICP theme."""
    name: str
    description: str
    signal_keywords: List[str]
    signal_phrases: List[str]


THEME_DEFINITIONS = {
    ThemeEnum.PRICING_SENSITIVITY: ThemeDefinition(
        name="Pricing Sensitivity",
        description="Customer concerned about cost, ROI, or pricing structure",
        signal_keywords=[
            "price", "pricing", "cost", "expensive", "cheap", "budget", "afford", "roi",
            "value", "expensive", "costly", "charge", "fee", "subscription"
        ],
        signal_phrases=[
            "too expensive", "high price", "cheaper than", "can't afford", "roi unclear",
            "price point", "pricing model", "cost benefit"
        ]
    ),
    ThemeEnum.COMPETITIVE_PRESSURE: ThemeDefinition(
        name="Competitive Pressure",
        description="Mentions of competitors or alternative solutions",
        signal_keywords=[
            "competitor", "alternative", "switch", "replace", "similar", "competitor",
            "other", "instead", "versus", "vs", "comparison"
        ],
        signal_phrases=[
            "switching to", "considering alternative", "compared to", "vs competitor",
            "your competitor", "other solutions", "competitor offers"
        ]
    ),
    ThemeEnum.FEATURE_PARITY: ThemeDefinition(
        name="Feature Parity",
        description="Missing features or capabilities that competitors have",
        signal_keywords=[
            "feature", "capability", "function", "ability", "support", "lacks", "missing",
            "doesn't have", "no", "unavailable"
        ],
        signal_phrases=[
            "we need", "don't have", "missing feature", "can't do", "not available",
            "wish you had", "lacks support for"
        ]
    ),
    ThemeEnum.IMPLEMENTATION_FRICTION: ThemeDefinition(
        name="Implementation Friction",
        description="Difficulties with setup, integration, or adoption",
        signal_keywords=[
            "implement", "integration", "setup", "configure", "deploy", "onboard",
            "difficult", "hard", "complex", "confusing", "steep", "learning"
        ],
        signal_phrases=[
            "hard to set up", "difficult to implement", "steep learning curve",
            "complex integration", "confusing onboarding", "takes too long"
        ]
    ),
    ThemeEnum.SUPPORT_EXPECTATIONS: ThemeDefinition(
        name="Support Expectations",
        description="Support quality, responsiveness, or expectations mismatch",
        signal_keywords=[
            "support", "help", "response", "time", "service", "customer", "slow",
            "quick", "fast", "responsive", "waiting", "ticket"
        ],
        signal_phrases=[
            "slow support", "no response", "response time", "support quality",
            "never responds", "can't get help", "support is poor"
        ]
    ),
}


def get_theme_definition(theme: ThemeEnum) -> ThemeDefinition:
    """Get the definition for a theme.

    Args:
        theme: The theme enum value

    Returns:
        ThemeDefinition with metadata
    """
    return THEME_DEFINITIONS[theme]


def tag_themes(text: str, min_keyword_matches: int = 1) -> List[str]:
    """Identify themes present in feedback text.

    Uses keyword matching and phrase detection to identify themes.

    Args:
        text: The feedback text to analyze
        min_keyword_matches: Minimum keyword matches to tag a theme

    Returns:
        List of theme enum values that matched
    """
    if not text:
        return []

    text_lower = text.lower()
    matched_themes: Set[str] = set()

    for theme, definition in THEME_DEFINITIONS.items():
        keyword_matches = 0

        # Check for keyword matches
        for keyword in definition.signal_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                keyword_matches += 1

        # Check for phrase matches (count as multiple keyword matches)
        for phrase in definition.signal_phrases:
            if phrase.lower() in text_lower:
                keyword_matches += 2  # Phrase matches weighted higher

        if keyword_matches >= min_keyword_matches:
            matched_themes.add(theme.value)

    return sorted(list(matched_themes))


def get_all_themes() -> dict:
    """Get all theme definitions.

    Returns:
        Dictionary of all themes and their definitions
    """
    return THEME_DEFINITIONS
