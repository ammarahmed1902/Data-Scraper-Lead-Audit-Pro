"""HTTP request/response logging middleware."""

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger("http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid.uuid4())[:8])
        path = request.url.path
        method = request.method
        started = time.perf_counter()

        logger.info(
            "request_start",
            request_id=request_id,
            method=method,
            path=path,
            client=request.client.host if request.client else None,
        )

        if path.endswith("/auth/login") and method == "POST":
            logger.info("auth_login_received", request_id=request_id)

        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.exception(
                "request_failed",
                request_id=request_id,
                method=method,
                path=path,
                elapsed_ms=elapsed_ms,
                error=str(exc),
            )
            raise

        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.info(
            "request_complete",
            request_id=request_id,
            method=method,
            path=path,
            status=response.status_code,
            elapsed_ms=elapsed_ms,
        )

        response.headers["X-Request-Id"] = request_id
        return response
