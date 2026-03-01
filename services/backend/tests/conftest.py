"""Shared pytest fixtures for all tests."""

import os

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base


@pytest.fixture(scope="session", autouse=True)
def set_test_env_vars():
    """Set required environment variables with test defaults for CI environments."""
    defaults = {
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret-only-not-for-production",
        "SMTP_HOST": "localhost",
        "SMTP_USER": "test@example.com",
        "SMTP_PASSWORD": "test-password",
        "SMTP_FROM": "test@example.com",
        "LLM_PROVIDER": "ollama",
        "LLM_API_URL": "http://localhost:11434",
        "LLM_OLLAMA_GENERATION_MODEL": "llama3",
        "LLM_OLLAMA_UTILITY_MODEL": "llama3",
        "LLM_LITELLM_GENERATION_MODEL": "gpt-4o",
        "LLM_LITELLM_UTILITY_MODEL": "gpt-4o-mini",
    }
    for key, value in defaults.items():
        os.environ.setdefault(key, value)


@pytest.fixture(scope="function")
async def test_engine():
    """
    Create an async SQLite in-memory database engine for testing.

    Uses StaticPool to ensure the same connection is reused,
    which is necessary for in-memory SQLite databases.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_engine):
    """
    Provide a clean database session for each test.

    The session is rolled back after each test to ensure isolation.
    """
    async_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        yield session
        await session.rollback()
