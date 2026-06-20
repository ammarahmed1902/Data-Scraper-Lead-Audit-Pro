"""Database and API error helpers."""

from __future__ import annotations

import structlog
from fastapi import HTTPException, status
from sqlalchemy.exc import OperationalError, ProgrammingError

logger = structlog.get_logger(__name__)

SCHEMA_MIGRATION_HINT = (
    "Database schema is out of date. Run migrations from the backend directory: "
    "python -m alembic upgrade head"
)


def is_schema_error(exc: BaseException) -> bool:
    message = str(exc).lower()
    markers = (
        "does not exist",
        "undefinedtableerror",
        "undefinedcolumnerror",
        "relation ",
        "column ",
    )
    return any(marker in message for marker in markers)


def schema_error_detail(exc: BaseException) -> str:
    raw = str(getattr(exc, "orig", exc))
    if "lead_discovery_searches" in raw or "discovered_leads" in raw:
        return (
            "Lead Discovery tables are missing. "
            + SCHEMA_MIGRATION_HINT
        )
    if is_schema_error(exc):
        return f"Database schema mismatch: {raw}. {SCHEMA_MIGRATION_HINT}"
    return SCHEMA_MIGRATION_HINT


def error_detail_from_exception(exc: BaseException) -> str:
    """Return the most useful message for API clients."""
    exc = root_cause(exc)

    if isinstance(exc, HTTPException):
        detail = exc.detail
        if isinstance(detail, str):
            return detail
        return str(detail)

    if isinstance(exc, ProgrammingError) and is_schema_error(exc):
        return schema_error_detail(exc)

    if isinstance(exc, OperationalError):
        return (
            "Database connection failed. Ensure PostgreSQL is running and "
            "DATABASE_URL credentials are correct."
        )

    message = str(exc).strip()
    return message or type(exc).__name__


def root_cause(exc: BaseException) -> BaseException:
    """Unwrap ExceptionGroup/TaskGroup wrappers and __cause__ chains."""
    if isinstance(exc, BaseExceptionGroup):
        if exc.exceptions:
            return root_cause(exc.exceptions[0])
    root = exc
    while root.__cause__ is not None:
        root = root.__cause__
    return root


def raise_for_database_error(exc: Exception, *, context: str) -> None:
    """Map SQLAlchemy and application errors to HTTP responses with real details."""
    detail = error_detail_from_exception(exc)

    logger.exception(
        "api_error",
        context=context,
        error_type=type(exc).__name__,
        error=detail,
    )

    if isinstance(exc, HTTPException):
        raise exc

    if isinstance(exc, ProgrammingError) and is_schema_error(exc):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        ) from exc

    if isinstance(exc, OperationalError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail,
    ) from exc
