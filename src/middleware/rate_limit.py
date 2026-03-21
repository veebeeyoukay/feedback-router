"""Rate limiting middleware using an in-memory token bucket."""

import time
from typing import Dict

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class _TokenBucket:
    """Simple token-bucket rate limiter for a single key."""

    __slots__ = ("max_tokens", "window_seconds", "tokens", "last_refill")

    def __init__(self, max_tokens: int, window_seconds: int):
        self.max_tokens = max_tokens
        self.window_seconds = window_seconds
        self.tokens = float(max_tokens)
        self.last_refill = time.monotonic()

    def consume(self) -> bool:
        """Try to consume one token.

        Returns:
            True if a token was available, False if rate limit exceeded.
        """
        now = time.monotonic()
        elapsed = now - self.last_refill

        # Refill tokens proportionally to elapsed time
        self.tokens = min(
            self.max_tokens,
            self.tokens + elapsed * (self.max_tokens / self.window_seconds),
        )
        self.last_refill = now

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False

    @property
    def retry_after(self) -> int:
        """Seconds until at least one token is available.

        Returns:
            Number of seconds to wait (ceiled to an integer).
        """
        if self.tokens >= 1.0:
            return 0
        deficit = 1.0 - self.tokens
        seconds = deficit / (self.max_tokens / self.window_seconds)
        return max(1, int(seconds) + 1)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP rate limiting middleware using an in-memory token bucket.

    Args:
        app: The ASGI application.
        max_requests: Maximum number of requests allowed within the window.
        window_seconds: Length of the sliding window in seconds.
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: Dict[str, _TokenBucket] = {}

    def _get_bucket(self, key: str) -> _TokenBucket:
        """Get or create a token bucket for the given key.

        Args:
            key: Identifier for the bucket (typically client IP).

        Returns:
            The token bucket for this key.
        """
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = _TokenBucket(self.max_requests, self.window_seconds)
            self._buckets[key] = bucket
        return bucket

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting.

        Args:
            request: HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response
        """
        # Skip rate limiting for health endpoint
        path = request.url.path.rstrip("/")
        if path == "/health":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        bucket = self._get_bucket(client_ip)

        if not bucket.consume():
            retry_after = bucket.retry_after
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
