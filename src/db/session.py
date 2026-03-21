"""Database session management using synchronous SQLAlchemy.

Provides engine creation, session factory, table initialisation, and a
``get_session`` generator suitable for FastAPI dependency injection.
"""

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.db.models import Base

# ---------------------------------------------------------------------------
# Database URL
# ---------------------------------------------------------------------------

_DEFAULT_DATABASE_URL = "postgresql://localhost:5432/feedback_router"


def get_db_url() -> str:
    """Return the database URL from the environment.

    Reads ``FEEDBACK_ROUTER_DATABASE_URL``.  Falls back to a sensible
    local-development default when the variable is not set.

    Returns:
        Database connection string.
    """
    return os.getenv("FEEDBACK_ROUTER_DATABASE_URL", _DEFAULT_DATABASE_URL)


# ---------------------------------------------------------------------------
# Engine & session factory  (created lazily on first use)
# ---------------------------------------------------------------------------

_engine = None
_SessionLocal = None


def _get_engine():
    """Create or return the cached SQLAlchemy engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            get_db_url(),
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=os.getenv("FEEDBACK_ROUTER_DATABASE_ECHO", "false").lower() == "true",
        )
    return _engine


def _get_session_factory() -> sessionmaker:
    """Create or return the cached session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=_get_engine(),
            autocommit=False,
            autoflush=False,
        )
    return _SessionLocal


# ---------------------------------------------------------------------------
# Lifecycle helpers (called from the FastAPI lifespan)
# ---------------------------------------------------------------------------


def init_db() -> None:
    """Create all tables defined in the ORM metadata.

    Safe to call repeatedly -- SQLAlchemy's ``create_all`` is a no-op
    for tables that already exist.
    """
    engine = _get_engine()
    Base.metadata.create_all(bind=engine)


def close_db() -> None:
    """Dispose of the engine's connection pool.

    Should be called during application shutdown to release all
    database connections cleanly.
    """
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _SessionLocal = None


# ---------------------------------------------------------------------------
# Dependency-injection helper
# ---------------------------------------------------------------------------


def get_session() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session and ensure it is closed afterwards.

    Intended for use as a FastAPI dependency::

        @app.get("/items")
        def list_items(db: Session = Depends(get_session)):
            ...

    Yields:
        A ``Session`` instance bound to the application engine.
    """
    factory = _get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()
