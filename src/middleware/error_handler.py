"""Error handling middleware and utilities."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorRecord:
    """Record of an error."""
    id: str
    timestamp: datetime
    error_type: str
    message: str
    severity: ErrorSeverity
    context: Dict[str, Any]
    feedback_id: Optional[str] = None
    stacktrace: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "error_type": self.error_type,
            "message": self.message,
            "severity": self.severity.value,
            "context": self.context,
            "feedback_id": self.feedback_id,
            "stacktrace": self.stacktrace,
            "retry_count": self.retry_count
        }


class DeadLetterQueue:
    """Queue for processing unprocessable feedback."""

    def __init__(self, max_size: int = 1000):
        """Initialize dead letter queue.

        Args:
            max_size: Maximum queue size
        """
        self.max_size = max_size
        self.queue: List[ErrorRecord] = []

    def add(self, error: ErrorRecord) -> bool:
        """Add error to queue.

        Args:
            error: Error record

        Returns:
            True if added successfully
        """
        if len(self.queue) >= self.max_size:
            # Remove oldest errors
            self.queue = self.queue[-(self.max_size - 1):]

        self.queue.append(error)
        return True

    def get_all(self) -> List[ErrorRecord]:
        """Get all queued errors.

        Returns:
            List of error records
        """
        return self.queue.copy()

    def get_by_severity(self, severity: ErrorSeverity) -> List[ErrorRecord]:
        """Get errors by severity.

        Args:
            severity: Severity level

        Returns:
            Filtered error records
        """
        return [e for e in self.queue if e.severity == severity]

    def get_by_feedback_id(self, feedback_id: str) -> List[ErrorRecord]:
        """Get errors for specific feedback.

        Args:
            feedback_id: Feedback ID

        Returns:
            Matching error records
        """
        return [e for e in self.queue if e.feedback_id == feedback_id]

    def retry(self, error_id: str) -> Optional[ErrorRecord]:
        """Retry processing an error.

        Args:
            error_id: Error ID

        Returns:
            Updated error record if found
        """
        for error in self.queue:
            if error.id == error_id:
                error.retry_count += 1
                return error
        return None

    def clear(self) -> None:
        """Clear the queue."""
        self.queue.clear()

    def size(self) -> int:
        """Get queue size.

        Returns:
            Number of items in queue
        """
        return len(self.queue)


class CircuitBreaker:
    """Circuit breaker for external integrations."""

    class State(str, Enum):
        """Circuit states."""
        CLOSED = "closed"
        OPEN = "open"
        HALF_OPEN = "half_open"

    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Failures before opening circuit
            reset_timeout: Seconds before attempting reset
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.state = self.State.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.success_count = 0

    def record_success(self) -> None:
        """Record successful call."""
        self.failure_count = 0
        if self.state == self.State.HALF_OPEN:
            self.state = self.State.CLOSED
            self.success_count = 0

    def record_failure(self) -> None:
        """Record failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = self.State.OPEN

    def is_available(self) -> bool:
        """Check if service is available.

        Returns:
            True if circuit allows calls
        """
        if self.state == self.State.CLOSED:
            return True

        if self.state == self.State.OPEN:
            # Check if timeout has passed for reset attempt
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed > self.reset_timeout:
                    self.state = self.State.HALF_OPEN
                    return True
            return False

        # HALF_OPEN state
        return True

    def get_state(self) -> str:
        """Get circuit state.

        Returns:
            Current state
        """
        return self.state.value


class ExternalIntegrationHealth:
    """Tracks health of external integrations."""

    def __init__(self):
        """Initialize health tracker."""
        self.services: Dict[str, CircuitBreaker] = {}

    def get_breaker(self, service_name: str) -> CircuitBreaker:
        """Get circuit breaker for service.

        Args:
            service_name: Name of service

        Returns:
            CircuitBreaker instance
        """
        if service_name not in self.services:
            self.services[service_name] = CircuitBreaker()
        return self.services[service_name]

    def record_success(self, service_name: str) -> None:
        """Record successful call to service.

        Args:
            service_name: Name of service
        """
        self.get_breaker(service_name).record_success()

    def record_failure(self, service_name: str) -> None:
        """Record failed call to service.

        Args:
            service_name: Name of service
        """
        self.get_breaker(service_name).record_failure()

    def is_available(self, service_name: str) -> bool:
        """Check if service is available.

        Args:
            service_name: Name of service

        Returns:
            True if available
        """
        return self.get_breaker(service_name).is_available()

    def get_status(self) -> Dict[str, str]:
        """Get status of all services.

        Returns:
            Dictionary of service statuses
        """
        return {
            name: breaker.get_state()
            for name, breaker in self.services.items()
        }


class ErrorHandler:
    """Central error handler."""

    def __init__(self):
        """Initialize error handler."""
        self.dlq = DeadLetterQueue()
        self.external_health = ExternalIntegrationHealth()

    def handle_processing_error(self, error_type: str, message: str,
                               context: Dict[str, Any],
                               feedback_id: Optional[str] = None,
                               stacktrace: Optional[str] = None) -> ErrorRecord:
        """Handle processing error.

        Args:
            error_type: Type of error
            message: Error message
            context: Error context
            feedback_id: Associated feedback ID
            stacktrace: Optional stacktrace

        Returns:
            ErrorRecord
        """
        severity = self._determine_severity(error_type, feedback_id)

        error = ErrorRecord(
            id=f"err_{datetime.utcnow().timestamp()}",
            timestamp=datetime.utcnow(),
            error_type=error_type,
            message=message,
            severity=severity,
            context=context,
            feedback_id=feedback_id,
            stacktrace=stacktrace
        )

        self.dlq.add(error)
        return error

    def handle_integration_error(self, service_name: str, error: Exception) -> None:
        """Handle external integration error.

        Args:
            service_name: Service name
            error: Exception raised
        """
        self.external_health.record_failure(service_name)

        self.handle_processing_error(
            error_type=f"integration_error_{service_name}",
            message=str(error),
            context={"service": service_name},
            stacktrace=str(error.__traceback__)
        )

    def _determine_severity(self, error_type: str, feedback_id: Optional[str]) -> ErrorSeverity:
        """Determine error severity.

        Args:
            error_type: Type of error
            feedback_id: Associated feedback ID

        Returns:
            ErrorSeverity
        """
        critical_errors = ["database", "auth", "payment", "security"]
        high_errors = ["integration", "timeout", "validation"]

        error_type_lower = error_type.lower()

        if any(critical in error_type_lower for critical in critical_errors):
            return ErrorSeverity.CRITICAL
        elif any(high in error_type_lower for high in high_errors):
            return ErrorSeverity.HIGH
        elif feedback_id:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    def get_dlq_stats(self) -> Dict[str, Any]:
        """Get dead letter queue statistics.

        Returns:
            DLQ statistics
        """
        all_errors = self.dlq.get_all()
        return {
            "total": len(all_errors),
            "by_severity": {
                "critical": len(self.dlq.get_by_severity(ErrorSeverity.CRITICAL)),
                "high": len(self.dlq.get_by_severity(ErrorSeverity.HIGH)),
                "medium": len(self.dlq.get_by_severity(ErrorSeverity.MEDIUM)),
                "low": len(self.dlq.get_by_severity(ErrorSeverity.LOW)),
            },
            "oldest_error": all_errors[0].timestamp.isoformat() if all_errors else None,
        }
