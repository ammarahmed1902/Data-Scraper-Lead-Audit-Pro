"""
Application entry point.
Registers middleware, routers, exception handlers, and lifecycle events.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy.exc import OperationalError

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import engine
from app.core.middleware import SecurityHeadersMiddleware
from app.core.rate_limit import limiter
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

    @app.exception_handler(OperationalError)
    async def database_operational_error_handler(
        request: Request, exc: OperationalError
    ):
        return JSONResponse(
            status_code=503,
            content={
                "detail": (
                    "Database connection failed. Ensure PostgreSQL is running and "
                    "DATABASE_URL credentials match your setup (see scripts/setup_postgres.sql)."
                )
            },
        )

    def _root_cause(exc: BaseException) -> BaseException:
        if isinstance(exc, BaseExceptionGroup):
            for sub in exc.exceptions:
                return _root_cause(sub)
        root = exc
        while root.__cause__ is not None:
            root = root.__cause__
        return root

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        root = _root_cause(exc)
        if type(root).__name__ == "InvalidPasswordError":
            return JSONResponse(
                status_code=503,
                content={
                    "detail": (
                        "PostgreSQL authentication failed for the configured database user. "
                        "Run backend/scripts/setup_postgres.sql as the postgres superuser."
                    )
                },
            )
        raise exc

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "version": settings.APP_VERSION}

    return app


app = create_app()
