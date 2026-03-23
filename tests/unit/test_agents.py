"""Unit tests for agent classes: IntakeAgent, ClassifierAgent, RouterAgent, ResponderAgent, ConciergeAgent."""

import pytest

from src.schemas.feedback import (
    FeedbackItem,
    FeedbackSource,
    FeedbackSourceEnum,
    FeedbackContact,
    ContactTypeEnum,
    FeedbackContent,
    FeedbackClassification,
    FeedbackLifecycle,
    FeedbackStatusEnum,
    FeedbackResponse,
    SentimentScore,
    PolarityEnum,
    UrgencyEnum,
    CategoryEnum,
    ResponseTypeEnum,
)
from src.schemas.routing import RoutingDecision
from src.agents.intake import IntakeAgent
from src.agents.classifier import ClassifierAgent
from src.agents.router import RouterAgent
from src.agents.responder import ResponderAgent
from src.agents.concierge import ConciergeAgent, ConciergeResponse


# ===========================================================================
# IntakeAgent tests
# ===========================================================================

class TestIntakeAgentNormalizeFeedback:
    """Test IntakeAgent.normalize_feedback() with raw input data."""

    def test_normalize_website_form_data(self, sample_raw_website_form):
        agent = IntakeAgent()
        item = agent.normalize_website_form(sample_raw_website_form)

        assert isinstance(item, FeedbackItem)
        assert item.id.startswith("fb_")
        assert item.source.channel == FeedbackSourceEnum.WEBSITE_FORM
        assert item.content.raw_text == sample_raw_website_form["message"]
        assert item.contact.name == "John Doe"
        assert item.lifecycle.status == FeedbackStatusEnum.RECEIVED

    def test_normalize_feedback_generates_unique_ids(self):
        agent = IntakeAgent()
        raw = {"text": "test", "id": "form_1"}
        item1 = agent.normalize_feedback(raw, "website_form")
        item2 = agent.normalize_feedback(raw, "website_form")
        assert item1.id != item2.id

    def test_normalize_feedback_with_email(self):
        agent = IntakeAgent()
        raw = {
            "text": "I need help",
            "email": "user@example.com",
            "name": "Test User",
            "id": "raw_001",
        }
        item = agent.normalize_feedback(raw, "website_form")
        assert item.contact.id == "user@example.com"

    def test_normalize_feedback_without_email_or_handle(self):
        agent = IntakeAgent()
        raw = {"text": "Anonymous feedback", "id": "raw_002"}
        item = agent.normalize_feedback(raw, "website_form")
        assert isinstance(item, FeedbackItem)

    def test_normalize_feedback_maps_channel_correctly(self):
        agent = IntakeAgent()
        channels = [
            ("website_form", FeedbackSourceEnum.WEBSITE_FORM),
            ("website_chat", FeedbackSourceEnum.WEBSITE_CHAT),
            ("website_404", FeedbackSourceEnum.WEBSITE_404),
            ("slack", FeedbackSourceEnum.SLACK),
            ("email", FeedbackSourceEnum.EMAIL),
        ]
        for channel_str, expected_enum in channels:
            raw = {"text": "test", "id": "test_id"}
            item = agent.normalize_feedback(raw, channel_str)
            assert item.source.channel == expected_enum, f"Channel {channel_str} mapping failed"

    def test_normalize_feedback_unknown_channel_defaults_to_email(self):
        agent = IntakeAgent()
        raw = {"text": "test", "id": "test_id"}
        item = agent.normalize_feedback(raw, "unknown_channel")
        assert item.source.channel == FeedbackSourceEnum.EMAIL

    def test_normalize_feedback_with_contact_db(self):
        contact_db = {
            "vip@bigcorp.com": {
                "type": ContactTypeEnum.CLIENT,
                "account_id": "acct_bigcorp",
            }
        }
        agent = IntakeAgent(contact_db=contact_db)
        raw = {
            "text": "Feedback from known client",
            "email": "vip@bigcorp.com",
            "id": "raw_003",
        }
        item = agent.normalize_feedback(raw, "email")
        assert item.contact.type == ContactTypeEnum.CLIENT


class TestIntakeAgentNormalizeSlackMessage:
    """Test IntakeAgent.normalize_slack_message()."""

    def test_normalize_slack_message(self, sample_raw_slack_message):
        agent = IntakeAgent()
        item = agent.normalize_slack_message(sample_raw_slack_message)

        assert isinstance(item, FeedbackItem)
        assert item.source.channel == FeedbackSourceEnum.SLACK
        assert item.content.raw_text == sample_raw_slack_message["text"]
        assert item.lifecycle.status == FeedbackStatusEnum.RECEIVED

    def test_normalize_slack_message_preserves_thread_ts(self):
        agent = IntakeAgent()
        data = {
            "ts": "12345",
            "text": "thread message",
            "user": "U123",
            "channel": "C456",
            "thread_ts": "11111.22222",
            "reactions": [],
        }
        item = agent.normalize_slack_message(data)
        assert item.source.context.get("thread_ts") == "11111.22222"


class TestIntakeAgentNormalizeEmail:
    """Test IntakeAgent.normalize_email()."""

    def test_normalize_email(self, sample_raw_email):
        agent = IntakeAgent()
        item = agent.normalize_email(sample_raw_email)

        assert isinstance(item, FeedbackItem)
        assert item.source.channel == FeedbackSourceEnum.EMAIL
        assert item.content.raw_text == sample_raw_email["body"]
        assert item.contact.name == "Alice Johnson"

    def test_normalize_email_preserves_subject_in_context(self, sample_raw_email):
        agent = IntakeAgent()
        item = agent.normalize_email(sample_raw_email)
        assert item.source.context.get("subject") == "Feature Request: Dark Mode"


# ===========================================================================
# ClassifierAgent tests
# ===========================================================================

class TestClassifierAgentClassify:
    """Test ClassifierAgent.classify() using rule-based path (use_llm=False)."""

    def _make_item(self, raw_text, contact_type=ContactTypeEnum.PROSPECT):
        return FeedbackItem(
            id="fb_cls_test",
            source=FeedbackSource(channel=FeedbackSourceEnum.WEBSITE_FORM, raw_id="cls_001"),
            contact=FeedbackContact(type=contact_type),
            content=FeedbackContent(raw_text=raw_text),
            lifecycle=FeedbackLifecycle(status=FeedbackStatusEnum.RECEIVED),
        )

    def test_classify_bug_text(self):
        agent = ClassifierAgent(use_llm=False)
        item = self._make_item("The dashboard is broken. I keep getting error messages and it crashes.")
        classification = agent.classify(item)
        assert classification.category == CategoryEnum.BUG

    def test_classify_feature_text(self):
        agent = ClassifierAgent(use_llm=False)
        item = self._make_item("We need the ability to add bulk export as a feature enhancement.")
        classification = agent.classify(item)
        assert classification.category == CategoryEnum.FEATURE

    def test_classify_complaint_text(self):
        agent = ClassifierAgent(use_llm=False)
        item = self._make_item("I'm very frustrated and disappointed with this terrible service.")
        classification = agent.classify(item)
        assert classification.category == CategoryEnum.COMPLAINT

    def test_classify_praise_text(self):
        agent = ClassifierAgent(use_llm=False)
        item = self._make_item("I love this product! It's amazing and excellent.")
        classification = agent.classify(item)
        assert classification.category == CategoryEnum.PRAISE

    def test_classify_returns_feedbackclassification(self):
        agent = ClassifierAgent(use_llm=False)
        item = self._make_item("Some text about the product.")
        classification = agent.classify(item)
        assert isinstance(classification, FeedbackClassification)

    def test_classify_returns_sentiment(self):
        agent = ClassifierAgent(use_llm=False)
        item = self._make_item("I hate this terrible product.")
        classification = agent.classify(item)
        assert classification.sentiment.polarity == PolarityEnum.NEGATIVE
        assert classification.sentiment.intensity > 0.3

    def test_classify_returns_themes(self):
        agent = ClassifierAgent(use_llm=False)
        item = self._make_item("Your pricing is too expensive, I'm switching to a competitor.")
        classification = agent.classify(item)
        assert isinstance(classification.themes, list)

    def test_classify_confidence_is_valid(self):
        agent = ClassifierAgent(use_llm=False)
        item = self._make_item("The product has a bug that crashes during export.")
        classification = agent.classify(item)
        assert 0.0 <= classification.confidence <= 1.0

    def test_classify_business_impact_for_client(self):
        agent = ClassifierAgent(use_llm=False)
        item = self._make_item(
            "The export is broken",
            contact_type=ContactTypeEnum.CLIENT,
        )
        classification = agent.classify(item)
        assert "Client satisfaction" in classification.business_impact or \
               "Product quality" in classification.business_impact

    def test_classify_fallback_when_no_llm(self):
        """When use_llm=True but no LLM client, should fall back to rules."""
        agent = ClassifierAgent(use_llm=True, llm_client=None)
        # The constructor should set use_llm=False when anthropic import fails
        item = self._make_item("The product has a bug that crashes during export.")
        classification = agent.classify(item)
        assert isinstance(classification, FeedbackClassification)


class TestClassifierAgentDetectCategory:
    """Test ClassifierAgent._detect_category() with keyword matching."""

    def test_detect_bug_category(self):
        agent = ClassifierAgent(use_llm=False)
        category = agent._detect_category("this has a bug and crashes with errors")
        assert category == CategoryEnum.BUG

    def test_detect_feature_category(self):
        agent = ClassifierAgent(use_llm=False)
        category = agent._detect_category("we need a new feature to add export capability")
        assert category == CategoryEnum.FEATURE

    def test_detect_question_category(self):
        agent = ClassifierAgent(use_llm=False)
        category = agent._detect_category("how do i use this? can you help me understand?")
        assert category == CategoryEnum.QUESTION

    def test_detect_complaint_category(self):
        agent = ClassifierAgent(use_llm=False)
        category = agent._detect_category("very frustrated and disappointed with your terrible service")
        assert category == CategoryEnum.COMPLAINT

    def test_detect_praise_category(self):
        agent = ClassifierAgent(use_llm=False)
        category = agent._detect_category("love this awesome excellent amazing product")
        assert category == CategoryEnum.PRAISE

    def test_detect_lost_category(self):
        agent = ClassifierAgent(use_llm=False)
        category = agent._detect_category("we are switching to a competitor and will cancel soon")
        assert category == CategoryEnum.LOST

    def test_detect_escalation_category(self):
        agent = ClassifierAgent(use_llm=False)
        category = agent._detect_category("this is urgent and critical, security compliance issue")
        assert category == CategoryEnum.ESCALATION

    def test_no_keywords_defaults_to_question(self):
        agent = ClassifierAgent(use_llm=False)
        category = agent._detect_category("the sky is blue today")
        assert category == CategoryEnum.QUESTION


# ===========================================================================
# RouterAgent tests
# ===========================================================================

class TestRouterAgent:
    """Test RouterAgent.route() end-to-end."""

    def _make_classified_item(self, category, urgency=UrgencyEnum.MEDIUM,
                               contact_type=ContactTypeEnum.PROSPECT):
        item = FeedbackItem(
            id="fb_router_test",
            source=FeedbackSource(channel=FeedbackSourceEnum.WEBSITE_FORM, raw_id="rt_001"),
            contact=FeedbackContact(type=contact_type),
            content=FeedbackContent(raw_text="Test feedback text"),
            lifecycle=FeedbackLifecycle(status=FeedbackStatusEnum.CLASSIFIED),
        )
        item.classification = FeedbackClassification(
            category=category,
            sentiment=SentimentScore(
                polarity=PolarityEnum.NEUTRAL,
                intensity=0.5,
                urgency=urgency,
            ),
            business_impact="Standard review",
            confidence=0.8,
            themes=[],
        )
        return item

    def test_route_returns_routing_decision(self):
        agent = RouterAgent()
        item = self._make_classified_item(CategoryEnum.BUG)
        decision = agent.route(item)
        assert isinstance(decision, RoutingDecision)

    def test_route_bug_to_support(self):
        agent = RouterAgent()
        item = self._make_classified_item(CategoryEnum.BUG)
        decision = agent.route(item)
        assert decision.assigned_team == "support"

    def test_route_feature_to_product(self):
        agent = RouterAgent()
        item = self._make_classified_item(CategoryEnum.FEATURE)
        decision = agent.route(item)
        assert decision.assigned_team == "product"

    def test_route_lost_to_sales(self):
        agent = RouterAgent()
        item = self._make_classified_item(CategoryEnum.LOST)
        decision = agent.route(item)
        assert decision.assigned_team == "sales"

    def test_route_complaint_to_customer_success(self):
        agent = RouterAgent()
        item = self._make_classified_item(CategoryEnum.COMPLAINT)
        decision = agent.route(item)
        assert decision.assigned_team == "customer_success"

    def test_route_unclassified_defaults(self):
        agent = RouterAgent()
        item = FeedbackItem(
            id="fb_unclassified",
            source=FeedbackSource(channel=FeedbackSourceEnum.WEBSITE_FORM, raw_id="un_001"),
            contact=FeedbackContact(type=ContactTypeEnum.UNKNOWN),
            content=FeedbackContent(raw_text="Unknown feedback"),
        )
        decision = agent.route(item)
        assert decision.assigned_team == "support"
        assert decision.response_type == "flag_human"


# ===========================================================================
# ResponderAgent tests
# ===========================================================================

class TestResponderAgent:
    """Test ResponderAgent.generate_response() for each response type."""

    def _make_item_with_classification(self, category=CategoryEnum.BUG,
                                        confidence=0.9):
        item = FeedbackItem(
            id="fb_resp_test",
            source=FeedbackSource(channel=FeedbackSourceEnum.EMAIL, raw_id="rsp_001"),
            contact=FeedbackContact(type=ContactTypeEnum.CLIENT),
            content=FeedbackContent(raw_text="This is a detailed feedback message for testing purposes."),
            lifecycle=FeedbackLifecycle(status=FeedbackStatusEnum.CLASSIFIED),
        )
        item.classification = FeedbackClassification(
            category=category,
            sentiment=SentimentScore(
                polarity=PolarityEnum.NEGATIVE, intensity=0.6, urgency=UrgencyEnum.MEDIUM,
            ),
            business_impact="Client satisfaction at risk",
            confidence=confidence,
            themes=[],
        )
        return item

    def test_generate_auto_acknowledge_response(self):
        agent = ResponderAgent()
        item = self._make_item_with_classification()
        decision = RoutingDecision(
            action="route_to_support",
            assigned_team="support",
            channel="email",
            recommended_action="Investigate bug",
            response_type="auto_acknowledge",
            priority=2,
        )
        response = agent.generate_response(item, decision)
        assert response.response_type == ResponseTypeEnum.AUTO_ACKNOWLEDGE
        assert response.auto_responded is True
        assert "support" in response.response_text.lower()

    def test_generate_draft_faq_response(self):
        agent = ResponderAgent()
        item = self._make_item_with_classification(category=CategoryEnum.BUG)
        decision = RoutingDecision(
            action="route_to_support",
            assigned_team="support",
            channel="email",
            recommended_action="Fix bug",
            response_type="draft_faq",
            priority=2,
        )
        response = agent.generate_response(item, decision)
        assert response.response_type == ResponseTypeEnum.DRAFT_FAQ
        assert response.auto_responded is False
        assert "DRAFT" in response.response_text

    def test_generate_draft_complex_response(self):
        agent = ResponderAgent()
        item = self._make_item_with_classification()
        decision = RoutingDecision(
            action="route_to_support",
            assigned_team="support",
            channel="email",
            recommended_action="Review concerns",
            response_type="draft_complex",
            priority=3,
        )
        response = agent.generate_response(item, decision)
        assert response.response_type == ResponseTypeEnum.DRAFT_COMPLEX
        assert response.auto_responded is False
        assert "DRAFT" in response.response_text
        assert "AWAITING HUMAN REVIEW" in response.response_text

    def test_generate_flag_human_response(self):
        agent = ResponderAgent()
        item = self._make_item_with_classification()
        decision = RoutingDecision(
            action="route_to_support",
            assigned_team="support",
            channel="email",
            recommended_action="Review",
            response_type="flag_human",
            priority=3,
        )
        response = agent.generate_response(item, decision)
        assert response.response_type == ResponseTypeEnum.FLAG_HUMAN
        assert response.auto_responded is False
        assert "FLAGGED FOR HUMAN REVIEW" in response.response_text

    def test_flag_human_includes_context(self):
        agent = ResponderAgent()
        item = self._make_item_with_classification()
        decision = RoutingDecision(
            action="route_to_support",
            assigned_team="support",
            channel="email",
            recommended_action="Review",
            response_type="flag_human",
            priority=2,
        )
        response = agent.generate_response(item, decision)
        assert "support" in response.response_text.lower()
        assert "Escalated" in response.response_text

    def test_unknown_response_type_defaults_to_flag_human(self):
        agent = ResponderAgent()
        # Test the internal mapping method directly since RoutingDecision
        # validates response_type via Pydantic enum
        result = agent._map_response_type("unknown_type")
        assert result == ResponseTypeEnum.FLAG_HUMAN


# ===========================================================================
# ConciergeAgent tests
# ===========================================================================

class TestConciergeAgent:
    """Test ConciergeAgent.handle_lost_visitor() for different frustration levels."""

    def _make_visitor_item(self, raw_text, contact_name=None):
        item = FeedbackItem(
            id="fb_concierge_test",
            source=FeedbackSource(channel=FeedbackSourceEnum.WEBSITE_FORM, raw_id="conc_001"),
            contact=FeedbackContact(type=ContactTypeEnum.UNKNOWN, name=contact_name),
            content=FeedbackContent(raw_text=raw_text),
            lifecycle=FeedbackLifecycle(status=FeedbackStatusEnum.RECEIVED),
        )
        return item

    def test_handle_frustrated_visitor(self):
        agent = ConciergeAgent()
        item = self._make_visitor_item(
            "I hate this terrible useless product! I'm so frustrated and angry.",
            contact_name="Sarah",
        )
        response = agent.handle_lost_visitor(item)

        assert isinstance(response, ConciergeResponse)
        assert response.tone == "empathetic_and_warm"
        assert response.should_escalate is True
        assert response.escalation_reason is not None
        assert "Sarah" in response.message

    def test_handle_confused_visitor(self):
        agent = ConciergeAgent()
        item = self._make_visitor_item(
            "I'm confused and lost. I can't find what I need. Help please.",
            contact_name="Bob",
        )
        response = agent.handle_lost_visitor(item)

        assert isinstance(response, ConciergeResponse)
        assert response.tone == "helpful_and_friendly"
        assert response.should_escalate is False
        assert "Bob" in response.message

    def test_handle_curious_visitor(self):
        agent = ConciergeAgent()
        item = self._make_visitor_item(
            "I just want to learn more about your product.",
            contact_name="Alice",
        )
        response = agent.handle_lost_visitor(item)

        assert isinstance(response, ConciergeResponse)
        assert response.tone == "warm_and_encouraging"
        assert response.should_escalate is False
        assert "Alice" in response.message

    def test_handle_visitor_without_name(self):
        agent = ConciergeAgent()
        item = self._make_visitor_item("Just browsing around.")
        response = agent.handle_lost_visitor(item)

        assert isinstance(response, ConciergeResponse)
        # Should use "there" as fallback name
        assert "there" in response.message

    def test_frustrated_visitor_gets_escalated(self):
        agent = ConciergeAgent()
        item = self._make_visitor_item(
            "This is terrible and useless. I'm angry and frustrated."
        )
        response = agent.handle_lost_visitor(item)
        assert response.should_escalate is True

    def test_confused_visitor_gets_resource_links(self):
        agent = ConciergeAgent()
        item = self._make_visitor_item(
            "I'm confused about the pricing and lost on the page."
        )
        response = agent.handle_lost_visitor(item)
        # Confused visitors should get guidance/resources
        assert "www.example.com" in response.message or "resource" in response.message.lower()

    def test_curious_visitor_gets_docs_links(self):
        agent = ConciergeAgent()
        item = self._make_visitor_item("I'm curious about your features.")
        response = agent.handle_lost_visitor(item)
        assert "docs" in response.message.lower() or "demo" in response.message.lower()


class TestConciergeAgentFrustrationDetection:
    """Test ConciergeAgent._detect_frustration() internal method."""

    def test_high_frustration(self):
        agent = ConciergeAgent()
        level = agent._detect_frustration("hate this terrible product, i'm so angry and frustrated")
        assert level == "high"

    def test_medium_frustration(self):
        agent = ConciergeAgent()
        level = agent._detect_frustration("i'm confused and lost, not sure what to do")
        assert level == "medium"

    def test_low_frustration(self):
        agent = ConciergeAgent()
        level = agent._detect_frustration("just browsing around, interesting product")
        assert level == "low"

    def test_single_high_word_is_medium(self):
        agent = ConciergeAgent()
        level = agent._detect_frustration("this is terrible")
        assert level == "medium"
