"""
Application entry point.
Registers middleware, routers, exception handlers, and lifecycle events.
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import engine
from app.core.middleware import SecurityHeadersMiddleware
from app.core.rate_limit import limiter
from app.core.db_errors import error_detail_from_exception, is_schema_error, root_cause, schema_error_detail
from app.core.redis import close_redis
from app.core.request_logging import RequestLoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    yield
    await close_redis()
    await engine.dispose()


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Cold-calling and lead-generation platform with automated website audits.",
        docs_url="/api/docs" if settings.APP_DEBUG else None,
        redoc_url="/api/redoc" if settings.APP_DEBUG else None,
        openapi_url="/api/openapi.json" if settings.APP_DEBUG else None,
        lifespan=lifespan,
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # Middleware (order matters: last added = first executed)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    @app.exception_handler(ProgrammingError)
    async def database_programming_error_handler(
        request: Request, exc: ProgrammingError
    ):
        if is_schema_error(exc):
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "message": schema_error_detail(exc),
                    "detail": schema_error_detail(exc),
                },
            )
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Database query failed.",
                "detail": str(exc.orig) if exc.orig else str(exc),
            },
        )

    @app.exception_handler(OperationalError)
    async def database_operational_error_handler(
        request: Request, exc: OperationalError
    ):
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "message": (
                    "Database connection failed. Ensure PostgreSQL is running and "
                    "DATABASE_URL credentials match your setup (see scripts/setup_postgres.sql)."
                ),
                "detail": (
                    "Database connection failed. Ensure PostgreSQL is running and "
                    "DATABASE_URL credentials match your setup (see scripts/setup_postgres.sql)."
                ),
            },
        )

    def _error_response(request: Request, exc: BaseException) -> JSONResponse:
        root = root_cause(exc)

        if isinstance(root, ProgrammingError) and is_schema_error(root):
            detail = schema_error_detail(root)
            return JSONResponse(
                status_code=503,
                content={"success": False, "message": detail, "detail": detail},
            )

        if isinstance(root, OperationalError):
            message = (
                "Database connection failed. Ensure PostgreSQL is running and "
                "DATABASE_URL credentials match your setup (see scripts/setup_postgres.sql)."
            )
            return JSONResponse(
                status_code=503,
                content={"success": False, "message": message, "detail": message},
            )

        if type(root).__name__ == "InvalidPasswordError":
            message = (
                "PostgreSQL authentication failed for the configured database user. "
                "Run backend/scripts/setup_postgres.sql as the postgres superuser."
            )
            return JSONResponse(
                status_code=503,
                content={"success": False, "message": message, "detail": message},
            )

        logger = structlog.get_logger(__name__)
        detail = error_detail_from_exception(root)
        logger.exception(
            "unhandled_exception",
            path=request.url.path,
            method=request.method,
            error_type=type(root).__name__,
            error=detail,
        )

        user_message = (
            f"Lead discovery failed: {detail}"
            if "/discovery" in request.url.path
            else f"Server error: {detail}"
        )
        payload: dict = {
            "success": False,
            "message": user_message,
            "detail": detail,
            "error_type": type(root).__name__,
            "source": request.url.path,
        }
        if settings.APP_DEBUG:
            payload["debug"] = {"type": type(root).__name__, "error": detail}
        return JSONResponse(status_code=500, content=payload)

    @app.exception_handler(ExceptionGroup)
    async def exception_group_handler(request: Request, exc: ExceptionGroup):
        """Starlette wraps middleware errors in TaskGroup / ExceptionGroup (Python 3.11+)."""
        return _error_response(request, exc)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return _error_response(request, exc)

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "version": settings.APP_VERSION}

    return app


app = create_app()
