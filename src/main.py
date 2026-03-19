"""FastAPI application entry point for Feedback Router."""

from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
import json

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.base import BaseHTTPMiddleware

from src.utils.config import get_config
from src.utils.logger import get_app_logger
from src.middleware.error_handler import ErrorHandler
from src.agents.intake import IntakeAgent
from src.agents.classifier import ClassifierAgent
from src.agents.router import RouterAgent
from src.agents.responder import ResponderAgent
from src.channels.website.webhook import WebsiteWebhookHandler, RateLimiter
from src.channels.slack.events import SlackEventHandler

logger = get_app_logger()
config = get_config()
error_handler = ErrorHandler()


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors."""

    async def dispatch(self, request: Request, call_next):
        """Process request with error handling.

        Args:
            request: HTTP request
            call_next: Next middleware

        Returns:
            HTTP response
        """
        try:
            response = await call_next(request)
            return response
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(
                "Unhandled exception in request",
                exception=exc,
                path=request.url.path,
                method=request.method
            )
            error_handler.handle_processing_error(
                error_type="http_error",
                message=str(exc),
                context={"path": request.url.path, "method": request.method}
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests."""

    async def dispatch(self, request: Request, call_next):
        """Log request details.

        Args:
            request: HTTP request
            call_next: Next middleware

        Returns:
            HTTP response
        """
        logger.debug(
            f"Incoming {request.method} request",
            path=request.url.path,
            client=request.client.host if request.client else "unknown"
        )

        response = await call_next(request)

        logger.debug(
            f"Response {response.status_code}",
            path=request.url.path,
            status_code=response.status_code
        )

        return response


# Initialize agents
intake_agent = IntakeAgent()
classifier_agent = ClassifierAgent(use_llm=False)
router_agent = RouterAgent()
responder_agent = ResponderAgent()

# Initialize channel handlers
website_webhook_handler = WebsiteWebhookHandler()
website_rate_limiter = RateLimiter(
    max_requests=config.webhook.rate_limit if config.webhook else 100,
    window_seconds=config.webhook.rate_limit_window if config.webhook else 60
)
slack_event_handler = SlackEventHandler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown.

    Args:
        app: FastAPI application
    """
    # Startup events
    logger.info(
        "Application starting",
        environment=config.environment,
        debug=config.debug
    )

    # Initialize connections
    if config.database:
        logger.info("Initializing database connection", url=config.database.url)
        # Database initialization would go here

    if config.redis:
        logger.info(
            "Initializing Redis connection",
            host=config.redis.host,
            port=config.redis.port
        )
        # Redis initialization would go here

    yield

    # Shutdown events
    logger.info("Application shutting down")

    # Close connections
    if config.database:
        logger.info("Closing database connection")
        # Database cleanup would go here

    if config.redis:
        logger.info("Closing Redis connection")
        # Redis cleanup would go here


# Create FastAPI app
app = FastAPI(
    title="Feedback Router API",
    description="ItsJen.ai's feedback routing system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if config.debug else ["https://itsjen.ai"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check() -> Dict[str, Any]:
    """Health check endpoint.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "feedback-router",
        "version": "1.0.0",
        "environment": config.environment,
        "external_services": error_handler.external_health.get_status()
    }


# Feedback processing endpoints
@app.post("/api/v1/feedback/intake", tags=["feedback"])
async def intake_feedback(raw_feedback: Dict[str, Any]) -> Dict[str, Any]:
    """Intake raw feedback.

    Args:
        raw_feedback: Raw feedback data

    Returns:
        Feedback item
    """
    try:
        channel = raw_feedback.get("channel", "email")
        feedback_item = intake_agent.normalize_feedback(raw_feedback, channel)

        logger.log_feedback_event(
            "intake",
            feedback_item.id,
            channel=channel,
            contact=feedback_item.contact.type.value
        )

        return {
            "feedback_id": feedback_item.id,
            "status": feedback_item.lifecycle.status.value,
            "contact_type": feedback_item.contact.type.value
        }
    except Exception as exc:
        logger.error("Error in feedback intake", exception=exc)
        error_handler.handle_processing_error(
            "intake_error",
            str(exc),
            raw_feedback
        )
        raise HTTPException(status_code=400, detail="Failed to intake feedback")


@app.post("/api/v1/feedback/{feedback_id}/classify", tags=["feedback"])
async def classify_feedback(feedback_id: str, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
    """Classify feedback.

    Args:
        feedback_id: Feedback ID
        feedback_data: Feedback data for classification

    Returns:
        Classification results
    """
    try:
        from src.schemas.feedback import FeedbackItem, FeedbackSource, FeedbackSourceEnum
        from src.schemas.feedback import FeedbackContact, ContactTypeEnum, FeedbackContent

        # Reconstruct feedback item from data
        feedback_item = FeedbackItem(
            id=feedback_id,
            source=FeedbackSource(
                channel=FeedbackSourceEnum.EMAIL,
                raw_id=feedback_id
            ),
            contact=FeedbackContact(
                type=ContactTypeEnum.UNKNOWN
            ),
            content=FeedbackContent(
                raw_text=feedback_data.get("text", "")
            )
        )

        classification = classifier_agent.classify(feedback_item)

        logger.log_classification(
            feedback_id,
            classification.category.value,
            classification.confidence
        )

        return {
            "feedback_id": feedback_id,
            "category": classification.category.value,
            "sentiment": {
                "polarity": classification.sentiment.polarity.value,
                "intensity": classification.sentiment.intensity,
                "urgency": classification.sentiment.urgency.value
            },
            "confidence": classification.confidence,
            "themes": classification.themes
        }
    except Exception as exc:
        logger.error("Error in classification", exception=exc, feedback_id=feedback_id)
        error_handler.handle_processing_error(
            "classification_error",
            str(exc),
            feedback_data,
            feedback_id=feedback_id
        )
        raise HTTPException(status_code=400, detail="Failed to classify feedback")


@app.post("/api/v1/feedback/{feedback_id}/route", tags=["feedback"])
async def route_feedback(feedback_id: str, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
    """Route feedback.

    Args:
        feedback_id: Feedback ID
        feedback_data: Feedback data for routing

    Returns:
        Routing decision
    """
    try:
        from src.schemas.feedback import FeedbackItem, FeedbackSource, FeedbackSourceEnum
        from src.schemas.feedback import FeedbackContact, ContactTypeEnum, FeedbackContent

        # Reconstruct feedback item
        feedback_item = FeedbackItem(
            id=feedback_id,
            source=FeedbackSource(
                channel=FeedbackSourceEnum.EMAIL,
                raw_id=feedback_id
            ),
            contact=FeedbackContact(
                type=ContactTypeEnum.UNKNOWN
            ),
            content=FeedbackContent(
                raw_text=feedback_data.get("text", "")
            )
        )

        routing_decision = router_agent.route(feedback_item)

        logger.log_routing(
            feedback_id,
            routing_decision.assigned_team or "unassigned",
            routing_decision.escalated
        )

        return {
            "feedback_id": feedback_id,
            "action": routing_decision.action,
            "assigned_team": routing_decision.assigned_team,
            "channel": routing_decision.channel,
            "escalated": routing_decision.escalated,
            "priority": routing_decision.priority
        }
    except Exception as exc:
        logger.error("Error in routing", exception=exc, feedback_id=feedback_id)
        error_handler.handle_processing_error(
            "routing_error",
            str(exc),
            feedback_data,
            feedback_id=feedback_id
        )
        raise HTTPException(status_code=400, detail="Failed to route feedback")


# Website webhook endpoints
@app.post("/webhooks/website/form", tags=["webhooks"])
async def website_form_submission(request: Request) -> Dict[str, Any]:
    """Handle website form submission.

    Args:
        request: HTTP request

    Returns:
        Response
    """
    try:
        # Check rate limit
        client_ip = request.client.host if request.client else "unknown"
        if not website_rate_limiter.is_allowed(client_ip):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        form_data = await request.json()
        signature = request.headers.get("X-Signature")

        feedback_item = website_webhook_handler.handle_form_submission(form_data, signature)

        logger.log_feedback_event(
            "website_form_submission",
            feedback_item.id,
            email=feedback_item.contact.name
        )

        return {
            "feedback_id": feedback_item.id,
            "status": "received"
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error in form submission", exception=exc)
        error_handler.handle_processing_error(
            "webhook_error",
            str(exc),
            {"type": "form_submission"}
        )
        raise HTTPException(status_code=400, detail="Failed to process form")


@app.post("/webhooks/website/chat", tags=["webhooks"])
async def website_chat_message(request: Request) -> Dict[str, Any]:
    """Handle website chat message.

    Args:
        request: HTTP request

    Returns:
        Response
    """
    try:
        client_ip = request.client.host if request.client else "unknown"
        if not website_rate_limiter.is_allowed(client_ip):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        chat_data = await request.json()
        signature = request.headers.get("X-Signature")

        feedback_item = website_webhook_handler.handle_chat_message(chat_data, signature)

        logger.log_feedback_event(
            "website_chat_message",
            feedback_item.id
        )

        return {
            "feedback_id": feedback_item.id,
            "status": "received"
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error in chat message", exception=exc)
        raise HTTPException(status_code=400, detail="Failed to process message")


@app.post("/webhooks/website/404", tags=["webhooks"])
async def website_404_feedback(request: Request) -> Dict[str, Any]:
    """Handle 404 page feedback.

    Args:
        request: HTTP request

    Returns:
        Response
    """
    try:
        client_ip = request.client.host if request.client else "unknown"
        if not website_rate_limiter.is_allowed(client_ip):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        page_data = await request.json()
        signature = request.headers.get("X-Signature")

        feedback_item = website_webhook_handler.handle_404_feedback(page_data, signature)

        logger.log_feedback_event(
            "website_404",
            feedback_item.id,
            page=page_data.get("requested_url")
        )

        return {
            "feedback_id": feedback_item.id,
            "status": "received"
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error in 404 feedback", exception=exc)
        raise HTTPException(status_code=400, detail="Failed to process 404 feedback")


# Slack endpoints
@app.post("/webhooks/slack/events", tags=["webhooks"])
async def slack_events(request: Request) -> Dict[str, Any]:
    """Handle Slack events.

    Args:
        request: HTTP request

    Returns:
        Response
    """
    try:
        data = await request.json()

        # Handle URL verification
        if data.get("type") == "url_verification":
            return {"challenge": data.get("challenge")}

        event = data.get("event", {})
        event_type = event.get("type")

        if event_type == "message":
            feedback_item = slack_event_handler.handle_message_event(event)
        elif event_type == "app_mention":
            feedback_item = slack_event_handler.handle_app_mention(event)
        elif event_type == "reaction_added":
            feedback_item = slack_event_handler.handle_reaction_added(event)
        else:
            return {"status": "ignored"}

        if feedback_item:
            logger.log_feedback_event(
                "slack_event",
                feedback_item.id,
                event_type=event_type
            )
            return {"status": "processed", "feedback_id": feedback_item.id}

        return {"status": "ignored"}

    except Exception as exc:
        logger.error("Error in Slack event", exception=exc)
        error_handler.handle_processing_error(
            "slack_webhook_error",
            str(exc),
            {}
        )
        raise HTTPException(status_code=400, detail="Failed to process Slack event")


# Monitoring and admin endpoints
@app.get("/api/v1/admin/dlq", tags=["admin"])
async def get_dlq_status() -> Dict[str, Any]:
    """Get dead letter queue status.

    Returns:
        DLQ statistics
    """
    return error_handler.get_dlq_stats()


@app.get("/api/v1/admin/integration-health", tags=["admin"])
async def get_integration_health() -> Dict[str, Any]:
    """Get external integration health.

    Returns:
        Integration health status
    """
    return {
        "integrations": error_handler.external_health.get_status()
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level=config.log_level.lower()
    )
