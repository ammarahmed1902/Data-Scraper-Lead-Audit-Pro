"""Synchronous SQLAlchemy session for Celery workers."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def _normalize_sync_url(url: str) -> str:
    """Use psycopg v3 driver when plain postgresql:// is configured."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


@lru_cache
def get_sync_engine() -> Engine:
    return create_engine(
        _normalize_sync_url(settings.DATABASE_URL_SYNC),
        echo=settings.APP_DEBUG,
        pool_size=10,
        max_overflow=5,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


@lru_cache
def _get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_sync_engine(),
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )


@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    session = _get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
