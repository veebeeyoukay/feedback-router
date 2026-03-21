"""API key authentication middleware."""

import os

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


# Paths that do not require authentication
EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Middleware that validates requests against an API key.

    Checks the X-API-Key header against the FEEDBACK_ROUTER_API_KEY
    environment variable.  Requests to health-check and documentation
    endpoints are allowed through without a key.
    """

    async def dispatch(self, request: Request, call_next):
        """Process request with API key validation.

        Args:
            request: HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response
        """
        # Skip authentication for exempt paths
        path = request.url.path.rstrip("/")
        if path in EXEMPT_PATHS:
            return await call_next(request)

        expected_key = os.environ.get("FEEDBACK_ROUTER_API_KEY")

        # If no key is configured, let the request through (opt-in security)
        if not expected_key:
            return await call_next(request)

        provided_key = request.headers.get("X-API-Key")

        if not provided_key or provided_key != expected_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or missing API key"},
            )

        return await call_next(request)
