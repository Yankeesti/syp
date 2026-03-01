"""Database configuration with async SQLAlchemy.

Based on: https://praciano.com.br/fastapi-and-async-sqlalchemy-20-with-pytest-done-right.html
"""

import contextlib
from typing import Any, AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    eager_defaults: Prevents implicit IO when using AsyncSession.
    See: https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html#preventing-implicit-io-when-using-asyncsession
    """

    __mapper_args__ = {"eager_defaults": True}


class DatabaseSessionManager:
    """Manages database engine and session lifecycle for async SQLAlchemy."""

    def __init__(self, host: str, engine_kwargs: dict[str, Any] = {}):
        self._engine = create_async_engine(host, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(
            autocommit=False,
            bind=self._engine,
            expire_on_commit=False,
        )

    async def close(self):
        """Close database engine and clean up resources."""
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        """Get a database connection with automatic rollback on error."""
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Get a database session with automatic cleanup."""
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Initialize global session manager
sessionmanager = DatabaseSessionManager(
    settings.database_url,
    {"echo": settings.echo_sql},
)


async def get_db_session():
    """
    FastAPI dependency for getting async database session.

    Usage:
        from app.shared.dependencies import DBSessionDep

        @router.get("/items")
        async def get_items(db: DBSessionDep):
            ...
    """
    async with sessionmanager.session() as session:
        yield session
