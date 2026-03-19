"""Sentiment analysis for feedback."""

from enum import Enum
from dataclasses import dataclass
from typing import Tuple, List
import re


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


@dataclass
class SentimentSignals:
    """Sentiment signal definitions."""
    polarity: PolarityEnum
    intensity: float
    urgency: UrgencyEnum
    signal_words: List[str]
    intensifiers: List[str]


POSITIVE_SIGNALS = [
    "love", "great", "awesome", "excellent", "amazing", "wonderful", "fantastic",
    "perfect", "best", "impressed", "happy", "satisfied", "pleased", "delighted",
    "grateful", "appreciate", "recommend", "fantastic", "brilliant"
]

NEGATIVE_SIGNALS = [
    "hate", "bad", "terrible", "awful", "horrible", "disappointing", "frustrated",
    "angry", "upset", "unhappy", "dissatisfied", "problem", "issue", "broken",
    "doesn't work", "error", "fail", "worst", "useless", "waste"
]

INTENSIFIERS = [
    "very", "extremely", "incredibly", "so", "really", "absolutely", "totally",
    "completely", "utterly", "quite", "definitely", "certainly"
]

URGENCY_CRITICAL_SIGNALS = [
    "critical", "emergency", "urgent", "immediately", "asap", "right now",
    "blocking", "can't", "cannot", "security", "breach", "down", "crash",
    "executive", "ceo", "board", "churn"
]

URGENCY_HIGH_SIGNALS = [
    "high", "important", "asap", "soon", "quickly", "business impact",
    "major", "severe", "significant", "serious", "must", "should"
]

URGENCY_MEDIUM_SIGNALS = [
    "medium", "normal", "standard", "regular", "when possible", "soon",
    "would be nice", "helpful", "useful", "interesting"
]

# Negative intensifiers that amplify negative sentiment
NEGATIVE_INTENSIFIERS = [
    "never", "always", "constantly", "every time", "no way", "not at all",
    "completely broken", "totally useless", "absolutely terrible"
]


def analyze_sentiment(text: str) -> Tuple[PolarityEnum, float, UrgencyEnum]:
    """Analyze sentiment of feedback text.

    Args:
        text: The feedback text to analyze

    Returns:
        Tuple of (polarity, intensity 0-1, urgency)
    """
    if not text:
        return PolarityEnum.NEUTRAL, 0.5, UrgencyEnum.MEDIUM

    text_lower = text.lower()

    # Count positive and negative signals
    positive_count = sum(1 for word in POSITIVE_SIGNALS if re.search(r'\b' + re.escape(word) + r'\b', text_lower))
    negative_count = sum(1 for word in NEGATIVE_SIGNALS if re.search(r'\b' + re.escape(word) + r'\b', text_lower))

    # Check for intensifiers
    intensifier_count = sum(1 for word in INTENSIFIERS if re.search(r'\b' + re.escape(word) + r'\b', text_lower))
    negative_intensifier_count = sum(1 for phrase in NEGATIVE_INTENSIFIERS if phrase.lower() in text_lower)

    # Determine polarity
    if positive_count > negative_count:
        polarity = PolarityEnum.POSITIVE
    elif negative_count > positive_count:
        polarity = PolarityEnum.NEGATIVE
    elif positive_count > 0 or negative_count > 0:
        polarity = PolarityEnum.MIXED
    else:
        polarity = PolarityEnum.NEUTRAL

    # Calculate intensity
    total_signals = positive_count + negative_count
    if total_signals == 0:
        intensity = 0.5
    else:
        # Base intensity from signal count
        intensity = min(0.3 + (total_signals * 0.1), 0.95)

        # Boost intensity for intensifiers
        intensity += (intensifier_count * 0.1)
        intensity += (negative_intensifier_count * 0.15)
        intensity = min(intensity, 0.99)

    # Determine urgency
    urgency = detect_urgency(text_lower, polarity, intensity)

    return polarity, min(max(intensity, 0.0), 1.0), urgency


def detect_urgency(text_lower: str, polarity: PolarityEnum, intensity: float) -> UrgencyEnum:
    """Detect urgency level from text.

    Args:
        text_lower: Lowercased feedback text
        polarity: Detected sentiment polarity
        intensity: Sentiment intensity

    Returns:
        UrgencyEnum representing urgency level
    """
    # Check for critical signals
    critical_matches = sum(1 for signal in URGENCY_CRITICAL_SIGNALS
                          if re.search(r'\b' + re.escape(signal) + r'\b', text_lower))

    if critical_matches > 0:
        return UrgencyEnum.CRITICAL

    # Check for high urgency signals
    high_matches = sum(1 for signal in URGENCY_HIGH_SIGNALS
                       if re.search(r'\b' + re.escape(signal) + r'\b', text_lower))

    if high_matches >= 2:
        return UrgencyEnum.HIGH

    # Negative sentiment with high intensity = high urgency
    if polarity == PolarityEnum.NEGATIVE and intensity > 0.7:
        return UrgencyEnum.HIGH

    # Check for medium urgency signals
    medium_matches = sum(1 for signal in URGENCY_MEDIUM_SIGNALS
                         if re.search(r'\b' + re.escape(signal) + r'\b', text_lower))

    if medium_matches > 0:
        return UrgencyEnum.MEDIUM

    # Default based on intensity and polarity
    if polarity == PolarityEnum.NEGATIVE and intensity > 0.5:
        return UrgencyEnum.MEDIUM

    return UrgencyEnum.LOW
