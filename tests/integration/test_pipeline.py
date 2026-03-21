"""Integration tests for the full feedback pipeline: intake -> classify -> route -> respond."""

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
from src.agents.concierge import ConciergeAgent


# ===========================================================================
# End-to-end pipeline tests
# ===========================================================================

class TestEndToEndPipeline:
    """Test raw feedback -> intake -> classify -> route -> respond flow."""

    def _run_pipeline(self, raw_input, channel, contact_db=None):
        """Run the full pipeline and return all intermediate results."""
        intake = IntakeAgent(contact_db=contact_db)
        classifier = ClassifierAgent(use_llm=False)
        router = RouterAgent()
        responder = ResponderAgent()

        # Step 1: Intake
        feedback_item = intake.normalize_feedback(raw_input, channel)
        assert isinstance(feedback_item, FeedbackItem)
        assert feedback_item.lifecycle.status == FeedbackStatusEnum.RECEIVED

        # Step 2: Classify
        classification = classifier.classify(feedback_item)
        feedback_item.classification = classification
        assert isinstance(classification, FeedbackClassification)

        # Step 3: Route
        routing_decision = router.route(feedback_item)
        assert isinstance(routing_decision, RoutingDecision)

        # Step 4: Respond
        response = responder.generate_response(feedback_item, routing_decision)
        assert isinstance(response, FeedbackResponse)

        return feedback_item, classification, routing_decision, response

    def test_bug_report_pipeline(self):
        """Bug report flows through to support team."""
        raw = {
            "id": "form_bug",
            "text": "The export feature has a bug. It crashes with an error every time I try to download.",
            "name": "Bug Reporter",
            "email": "bugs@example.com",
        }
        item, classification, routing, response = self._run_pipeline(raw, "website_form")

        assert classification.category == CategoryEnum.BUG
        assert routing.assigned_team == "support"
        assert response.response_type in [
            ResponseTypeEnum.AUTO_ACKNOWLEDGE,
            ResponseTypeEnum.DRAFT_FAQ,
            ResponseTypeEnum.DRAFT_COMPLEX,
            ResponseTypeEnum.FLAG_HUMAN,
        ]

    def test_feature_request_pipeline(self):
        """Feature request flows through to product team."""
        raw = {
            "id": "form_feature",
            "text": "We need a new feature for bulk export capability. Please add this enhancement.",
            "name": "Feature Requester",
            "email": "features@example.com",
        }
        item, classification, routing, response = self._run_pipeline(raw, "website_form")

        assert classification.category == CategoryEnum.FEATURE
        assert routing.assigned_team == "product"

    def test_complaint_pipeline(self):
        """Complaint flows through to customer success."""
        raw = {
            "id": "form_complaint",
            "text": "I'm very frustrated and disappointed with your terrible service. This is unacceptable and poor quality.",
            "name": "Unhappy Customer",
            "email": "unhappy@example.com",
        }
        item, classification, routing, response = self._run_pipeline(raw, "website_form")

        assert classification.category == CategoryEnum.COMPLAINT
        assert routing.assigned_team == "customer_success"
        assert classification.sentiment.polarity == PolarityEnum.NEGATIVE

    def test_praise_pipeline(self):
        """Praise flows through to customer success."""
        raw = {
            "id": "form_praise",
            "text": "I love this product! It's amazing and excellent. Best tool we've used.",
            "name": "Happy Customer",
            "email": "happy@example.com",
        }
        item, classification, routing, response = self._run_pipeline(raw, "website_form")

        assert classification.category == CategoryEnum.PRAISE
        assert routing.assigned_team == "customer_success"
        assert classification.sentiment.polarity == PolarityEnum.POSITIVE

    def test_lost_customer_pipeline(self):
        """Lost/churn risk flows through to sales with escalation."""
        raw = {
            "id": "form_lost",
            "text": "We are switching to a competitor and considering canceling our subscription. Looking at alternative solutions.",
            "name": "Leaving Customer",
            "email": "leaving@example.com",
        }
        item, classification, routing, response = self._run_pipeline(raw, "website_form")

        assert classification.category == CategoryEnum.LOST
        assert routing.assigned_team == "sales"

    def test_escalation_pipeline(self):
        """Escalation-worthy feedback gets escalated."""
        raw = {
            "id": "form_escalation",
            "text": "This is urgent and critical. We found a security compliance issue that needs immediate executive attention.",
            "name": "Security Team Lead",
            "email": "security@bigcorp.com",
        }
        item, classification, routing, response = self._run_pipeline(raw, "website_form")

        assert classification.category == CategoryEnum.ESCALATION
        assert routing.escalated is True

    def test_slack_channel_pipeline(self):
        """Slack feedback preserves channel in routing."""
        raw = {
            "id": "slack_001",
            "text": "The API has a bug. Getting error 500 on the dashboard endpoint.",
            "slack_handle": "user123",
        }
        item, classification, routing, response = self._run_pipeline(raw, "slack")

        assert item.source.channel == FeedbackSourceEnum.SLACK
        assert routing.channel == "slack"

    def test_email_channel_pipeline(self):
        """Email feedback preserves channel in routing."""
        raw = {
            "id": "email_001",
            "text": "How do I reset my password? Can you help me understand the process?",
            "name": "Email User",
            "email": "emailuser@example.com",
        }
        item, classification, routing, response = self._run_pipeline(raw, "email")

        assert item.source.channel == FeedbackSourceEnum.EMAIL
        assert routing.channel == "email"


# ===========================================================================
# Different feedback types produce different routing decisions
# ===========================================================================

class TestDifferentRoutingDecisions:
    """Test that different feedback types produce distinct routing decisions."""

    def _classify_and_route(self, text, channel="website_form"):
        intake = IntakeAgent()
        classifier = ClassifierAgent(use_llm=False)
        router = RouterAgent()

        item = intake.normalize_feedback({"id": "test", "text": text}, channel)
        classification = classifier.classify(item)
        item.classification = classification
        decision = router.route(item)
        return classification, decision

    def test_bug_vs_feature_different_teams(self):
        _, bug_routing = self._classify_and_route(
            "The system crashes with a bug error when I try to export."
        )
        _, feature_routing = self._classify_and_route(
            "We need the ability to add custom features and enhancements."
        )
        assert bug_routing.assigned_team != feature_routing.assigned_team

    def test_complaint_vs_praise_different_sentiment(self):
        complaint_cls, _ = self._classify_and_route(
            "Terrible service. I'm frustrated and disappointed."
        )
        praise_cls, _ = self._classify_and_route(
            "Excellent amazing product. I love it."
        )
        assert complaint_cls.sentiment.polarity != praise_cls.sentiment.polarity

    def test_high_urgency_vs_low_urgency_different_priority(self):
        _, high_routing = self._classify_and_route(
            "CRITICAL: Security breach detected. System is down. This is an emergency."
        )
        _, low_routing = self._classify_and_route(
            "Just sharing some thoughts on the color scheme."
        )
        assert high_routing.priority < low_routing.priority  # lower number = higher priority

    def test_lost_customer_gets_escalated(self):
        _, routing = self._classify_and_route(
            "We are canceling and switching to a competitor. Looking at alternatives."
        )
        assert routing.escalated is True

    def test_simple_question_not_escalated(self):
        _, routing = self._classify_and_route(
            "How do I reset my password?"
        )
        assert routing.escalated is False


# ===========================================================================
# Escalation triggers in full pipeline context
# ===========================================================================

class TestEscalationInPipeline:
    """Test that escalation triggers work within the full pipeline."""

    def _run_through_router(self, text, channel="website_form"):
        intake = IntakeAgent()
        classifier = ClassifierAgent(use_llm=False)
        router = RouterAgent()

        item = intake.normalize_feedback({"id": "esc_test", "text": text}, channel)
        classification = classifier.classify(item)
        item.classification = classification
        return router.route(item)

    def test_security_mention_triggers_escalation(self):
        decision = self._run_through_router(
            "We found a security vulnerability in the login endpoint."
        )
        assert decision.escalated is True

    def test_executive_mention_triggers_escalation(self):
        decision = self._run_through_router(
            "Our CEO is concerned about the product roadmap."
        )
        assert decision.escalated is True

    def test_churn_language_triggers_escalation(self):
        decision = self._run_through_router(
            "We are going to cancel our subscription and switch to Competitor X."
        )
        assert decision.escalated is True

    def test_high_intensity_negative_triggers_escalation(self):
        decision = self._run_through_router(
            "I absolutely hate this terrible product. It's the worst thing ever. "
            "Completely useless and totally broken. Never works."
        )
        assert decision.escalated is True

    def test_positive_simple_feedback_no_escalation(self):
        decision = self._run_through_router(
            "Thanks for the update, the new color scheme looks nice."
        )
        assert decision.escalated is False

    def test_contract_renewal_concern_triggers_escalation(self):
        decision = self._run_through_router(
            "Our contract renewal is coming up and we have major concerns about the product."
        )
        assert decision.escalated is True


# ===========================================================================
# Concierge pipeline integration
# ===========================================================================

class TestConciergePipelineIntegration:
    """Test concierge agent works within pipeline context."""

    def test_lost_visitor_gets_concierge_response(self):
        intake = IntakeAgent()
        concierge = ConciergeAgent()

        raw = {
            "id": "visitor_001",
            "text": "I'm confused and lost. I can't find what I need. Help please.",
            "name": "Lost Visitor",
        }
        item = intake.normalize_feedback(raw, "website_form")

        response = concierge.handle_lost_visitor(item)
        assert response.should_escalate is False
        assert "Lost Visitor" in response.message

    def test_frustrated_visitor_gets_escalation(self):
        intake = IntakeAgent()
        concierge = ConciergeAgent()

        raw = {
            "id": "visitor_002",
            "text": "I hate this terrible useless website! I'm so angry and frustrated!",
            "name": "Angry Visitor",
        }
        item = intake.normalize_feedback(raw, "website_form")

        response = concierge.handle_lost_visitor(item)
        assert response.should_escalate is True
        assert "Angry Visitor" in response.message


# ===========================================================================
# Website form pipeline integration
# ===========================================================================

class TestWebsiteFormPipelineIntegration:
    """Test full pipeline from website form handler through routing."""

    def test_website_form_full_pipeline(self):
        from src.channels.website.webhook import WebsiteWebhookHandler

        handler = WebsiteWebhookHandler()
        classifier = ClassifierAgent(use_llm=False)
        router = RouterAgent()
        responder = ResponderAgent()

        form_data = {
            "name": "Pipeline User",
            "email": "pipeline@example.com",
            "message": "The dashboard has a bug and keeps crashing with error messages.",
            "page_url": "https://example.com/dashboard",
        }

        # Step 1: Webhook handler creates FeedbackItem
        item = handler.handle_form_submission(form_data)
        assert isinstance(item, FeedbackItem)

        # Step 2: Classify
        classification = classifier.classify(item)
        item.classification = classification

        # Step 3: Route
        decision = router.route(item)
        assert decision.assigned_team == "support"

        # Step 4: Respond
        response = responder.generate_response(item, decision)
        assert isinstance(response, FeedbackResponse)


# ===========================================================================
# Slack pipeline integration
# ===========================================================================

class TestSlackPipelineIntegration:
    """Test full pipeline from Slack event handler through routing."""

    def test_slack_message_full_pipeline(self):
        from src.channels.slack.events import SlackEventHandler

        handler = SlackEventHandler()
        classifier = ClassifierAgent(use_llm=False)
        router = RouterAgent()
        responder = ResponderAgent()

        event_data = {
            "channel": "feedback",
            "channel_name": "feedback",
            "ts": "12345.67890",
            "text": "We need a new feature for bulk data export. Please add this capability.",
            "user": "USLACK",
        }

        # Step 1: Slack handler creates FeedbackItem
        item = handler.handle_message_event(event_data)
        assert isinstance(item, FeedbackItem)

        # Step 2: Classify
        classification = classifier.classify(item)
        item.classification = classification

        # Step 3: Route
        decision = router.route(item)
        assert decision.assigned_team == "product"
        assert decision.channel == "slack"

        # Step 4: Respond
        response = responder.generate_response(item, decision)
        assert isinstance(response, FeedbackResponse)
