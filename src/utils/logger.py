"""Structured logging setup with structlog."""

import logging
import sys
from typing import Any, Dict, Optional
import json
from datetime import datetime


class StructuredLogger:
    """Structured logging with JSON output."""

    def __init__(self, name: str, level: str = "INFO"):
        """Initialize structured logger.

        Args:
            name: Logger name
            level: Log level
        """
        self.name = name
        self.level = getattr(logging, level.upper(), logging.INFO)
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)

        # Remove existing handlers
        self.logger.handlers.clear()

        # Add JSON handler
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _build_log_record(self, level: str, message: str,
                         extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build structured log record.

        Args:
            level: Log level
            message: Log message
            extra: Extra context

        Returns:
            Log record dictionary
        """
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "logger": self.name,
            "message": message,
        }

        if extra:
            record["context"] = extra

        return record

    def _log(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Internal logging method.

        Args:
            level: Log level
            message: Log message
            extra: Extra context
        """
        record = self._build_log_record(level, message, extra)
        log_message = json.dumps(record)

        if level == "DEBUG":
            self.logger.debug(log_message)
        elif level == "INFO":
            self.logger.info(log_message)
        elif level == "WARNING":
            self.logger.warning(log_message)
        elif level == "ERROR":
            self.logger.error(log_message)
        elif level == "CRITICAL":
            self.logger.critical(log_message)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message.

        Args:
            message: Log message
            **kwargs: Additional context
        """
        self._log("DEBUG", message, kwargs or None)

    def info(self, message: str, **kwargs) -> None:
        """Log info message.

        Args:
            message: Log message
            **kwargs: Additional context
        """
        self._log("INFO", message, kwargs or None)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message.

        Args:
            message: Log message
            **kwargs: Additional context
        """
        self._log("WARNING", message, kwargs or None)

    def error(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log error message.

        Args:
            message: Log message
            exception: Optional exception
            **kwargs: Additional context
        """
        if exception:
            kwargs["exception"] = str(exception)
            kwargs["exception_type"] = type(exception).__name__

        self._log("ERROR", message, kwargs or None)

    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log critical message.

        Args:
            message: Log message
            exception: Optional exception
            **kwargs: Additional context
        """
        if exception:
            kwargs["exception"] = str(exception)
            kwargs["exception_type"] = type(exception).__name__

        self._log("CRITICAL", message, kwargs or None)

    def log_feedback_event(self, event_type: str, feedback_id: str, **context) -> None:
        """Log feedback-related event.

        Args:
            event_type: Type of event
            feedback_id: Feedback ID
            **context: Additional context
        """
        self.info(
            f"Feedback event: {event_type}",
            event_type=event_type,
            feedback_id=feedback_id,
            **context
        )

    def log_classification(self, feedback_id: str, category: str, confidence: float,
                          **context) -> None:
        """Log classification event.

        Args:
            feedback_id: Feedback ID
            category: Classified category
            confidence: Classification confidence
            **context: Additional context
        """
        self.info(
            "Feedback classified",
            feedback_id=feedback_id,
            category=category,
            confidence=confidence,
            **context
        )

    def log_routing(self, feedback_id: str, assigned_team: str, escalated: bool,
                   **context) -> None:
        """Log routing event.

        Args:
            feedback_id: Feedback ID
            assigned_team: Assigned team
            escalated: Whether escalated
            **context: Additional context
        """
        self.info(
            "Feedback routed",
            feedback_id=feedback_id,
            assigned_team=assigned_team,
            escalated=escalated,
            **context
        )

    def log_response_generated(self, feedback_id: str, response_type: str,
                             auto_sent: bool, **context) -> None:
        """Log response generation.

        Args:
            feedback_id: Feedback ID
            response_type: Type of response
            auto_sent: Whether auto-sent
            **context: Additional context
        """
        self.info(
            "Response generated",
            feedback_id=feedback_id,
            response_type=response_type,
            auto_sent=auto_sent,
            **context
        )


# Global logger instances
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str) -> StructuredLogger:
    """Get or create logger.

    Args:
        name: Logger name

    Returns:
        StructuredLogger instance
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)
    return _loggers[name]


# Convenience function for common logger
def get_app_logger() -> StructuredLogger:
    """Get application logger.

    Returns:
        StructuredLogger instance
    """
    return get_logger("feedback-router")
