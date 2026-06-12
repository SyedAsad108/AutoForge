"""
Request logging middleware for the AutoForge backend.

Logs method, path, status code, and latency for every request.
"""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from backend.core.logger import get_logger

logger = get_logger("RequestLogger")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Structured request/response logging with timing."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.monotonic()
        response = await call_next(request)
        elapsed_ms = (time.monotonic() - start) * 1000

        req_id = getattr(request.state, "request_id", "-")
        logger.info(
            f"{request.method} {request.url.path} "
            f"status={response.status_code} "
            f"latency={elapsed_ms:.1f}ms "
            f"req_id={req_id}"
        )
        return response
