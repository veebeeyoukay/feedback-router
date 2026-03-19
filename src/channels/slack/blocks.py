"""Slack Block Kit builders for rich feedback messages."""

from typing import Dict, Any, List, Optional
from src.schemas.feedback import FeedbackClassification, FeedbackItem


class SlackBlockBuilder:
    """Builds Slack Block Kit messages."""

    @staticmethod
    def build_feedback_routing_message(feedback_item: FeedbackItem) -> Dict[str, Any]:
        """Build rich feedback routing message.

        Args:
            feedback_item: Feedback item to display

        Returns:
            Slack message block
        """
        classification = feedback_item.classification

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📬 New Feedback Received",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*From:*\n{feedback_item.contact.name or 'Unknown'}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Type:*\n{feedback_item.contact.type.value}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Channel:*\n{feedback_item.source.channel.value}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{feedback_item.timestamp.strftime('%Y-%m-%d %H:%M')}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Feedback:*\n{feedback_item.content.raw_text[:300]}"
                }
            }
        ]

        # Add classification info if available
        if classification:
            blocks.append({
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Category:*\n{SlackBlockBuilder._get_category_emoji(classification.category.value)} {classification.category.value}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Sentiment:*\n{SlackBlockBuilder._get_sentiment_emoji(classification.sentiment.polarity.value)} {classification.sentiment.polarity.value}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Urgency:*\n{SlackBlockBuilder._get_urgency_emoji(classification.sentiment.urgency.value)} {classification.sentiment.urgency.value}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Confidence:*\n{int(classification.confidence * 100)}%"
                    }
                ]
            })

            # Add themes if present
            if classification.themes:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Themes:* {', '.join(classification.themes)}"
                    }
                })

        # Add action buttons
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✓ Acknowledge",
                        "emoji": True
                    },
                    "value": f"acknowledge_{feedback_item.id}",
                    "style": "primary"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "→ Assign",
                        "emoji": True
                    },
                    "value": f"assign_{feedback_item.id}"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "⬆ Escalate",
                        "emoji": True
                    },
                    "value": f"escalate_{feedback_item.id}",
                    "style": "danger"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✓ Resolve",
                        "emoji": True
                    },
                    "value": f"resolve_{feedback_item.id}"
                }
            ]
        })

        return {"blocks": blocks}

    @staticmethod
    def build_escalation_alert(feedback_item: FeedbackItem, reason: str) -> Dict[str, Any]:
        """Build escalation alert message.

        Args:
            feedback_item: Feedback item
            reason: Escalation reason

        Returns:
            Slack message block
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "⚠️ ESCALATION ALERT",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Reason:* {reason}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*From:* {feedback_item.contact.name or 'Unknown'}\n*Feedback:* {feedback_item.content.raw_text[:200]}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Details",
                            "emoji": True
                        },
                        "value": f"view_{feedback_item.id}",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Acknowledge",
                            "emoji": True
                        },
                        "value": f"ack_escalation_{feedback_item.id}"
                    }
                ]
            }
        ]

        return {"blocks": blocks}

    @staticmethod
    def build_daily_digest(feedback_items: List[FeedbackItem], stats: Dict[str, Any]) -> Dict[str, Any]:
        """Build daily digest message.

        Args:
            feedback_items: List of feedback items
            stats: Summary statistics

        Returns:
            Slack message block
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 Daily Feedback Digest",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Total Feedback:* {stats.get('total', 0)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Escalations:* {stats.get('escalations', 0)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Avg Sentiment:* {stats.get('avg_sentiment', 'N/A')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Pending Action:* {stats.get('pending', 0)}"
                    }
                ]
            }
        ]

        # Add top categories
        if stats.get('top_categories'):
            category_text = "\n".join(
                f"• {cat}: {count}"
                for cat, count in stats['top_categories'].items()
            )
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Top Categories:*\n{category_text}"
                }
            })

        # Add recent items
        if feedback_items:
            items_text = "\n".join(
                f"• {item.contact.name or 'Unknown'}: {item.content.raw_text[:60]}..."
                for item in feedback_items[:5]
            )
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Recent Feedback:*\n{items_text}"
                }
            })

        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View Full Report",
                        "emoji": True
                    },
                    "value": "view_full_report",
                    "style": "primary"
                }
            ]
        })

        return {"blocks": blocks}

    @staticmethod
    def _get_category_emoji(category: str) -> str:
        """Get emoji for category.

        Args:
            category: Category name

        Returns:
            Emoji string
        """
        emoji_map = {
            "bug": "🐛",
            "feature": "✨",
            "question": "❓",
            "complaint": "😞",
            "praise": "🎉",
            "suggestion": "💡",
            "lost": "🔍",
            "escalation": "⬆️"
        }
        return emoji_map.get(category, "📝")

    @staticmethod
    def _get_sentiment_emoji(polarity: str) -> str:
        """Get emoji for sentiment.

        Args:
            polarity: Sentiment polarity

        Returns:
            Emoji string
        """
        emoji_map = {
            "positive": "😊",
            "negative": "😞",
            "neutral": "😐",
            "mixed": "🤔"
        }
        return emoji_map.get(polarity, "💭")

    @staticmethod
    def _get_urgency_emoji(urgency: str) -> str:
        """Get emoji for urgency.

        Args:
            urgency: Urgency level

        Returns:
            Emoji string
        """
        emoji_map = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🔴",
            "critical": "🚨"
        }
        return emoji_map.get(urgency, "⚪")
