"""Shared fixtures for integration tests."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.core.security import create_jwt_token
from app.shared.schemas import TokenPayload
from tests.integration.helpers import build_default_quiz_output, build_expired_token


def pytest_collection_modifyitems(config, items):
    del config
    for item in items:
        if "tests/integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


@pytest.fixture
def test_user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def other_user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
async def app(monkeypatch, tmp_path_factory):
    db_path = tmp_path_factory.mktemp("db") / "test.sqlite"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("SMTP_HOST", "localhost")
    monkeypatch.setenv("SMTP_USER", "test@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "test-password")
    monkeypatch.setenv("SMTP_FROM", "test@example.com")
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_API_URL", "http://localhost:11434")
    monkeypatch.setenv("LLM_OLLAMA_GENERATION_MODEL", "llama3")
    monkeypatch.setenv("LLM_OLLAMA_UTILITY_MODEL", "llama3")
    monkeypatch.setenv("LLM_LITELLM_GENERATION_MODEL", "gpt-4o")
    monkeypatch.setenv("LLM_LITELLM_UTILITY_MODEL", "gpt-4o-mini")
    get_settings.cache_clear()

    import app.core.database as database
    import app.modules.quiz.services.quiz_service as quiz_service
    import app.models

    original_sessionmanager = database.sessionmanager
    original_quiz_sessionmanager = quiz_service.sessionmanager

    test_sessionmanager = database.DatabaseSessionManager(
        db_url,
        {"echo": False},
    )
    database.sessionmanager = test_sessionmanager
    quiz_service.sessionmanager = test_sessionmanager

    async with database.sessionmanager.connect() as conn:
        await conn.run_sync(database.Base.metadata.create_all)

    from app.main import app as fastapi_app
    from app.modules.quiz.public.ports import register_quiz_ports
    from app.modules.llm.public.ports import register_llm_ports

    register_quiz_ports(fastapi_app)
    register_llm_ports(fastapi_app)

    yield fastapi_app

    async with database.sessionmanager.connect() as conn:
        await conn.run_sync(database.Base.metadata.drop_all)
    await database.sessionmanager.close()

    database.sessionmanager = original_sessionmanager
    quiz_service.sessionmanager = original_quiz_sessionmanager
    fastapi_app.dependency_overrides.clear()
    get_settings.cache_clear()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as http_client:
        yield http_client


@pytest.fixture
def auth_headers(app):
    def _factory(user_id: uuid.UUID) -> dict[str, str]:
        token = create_jwt_token(TokenPayload(user_id=user_id))
        return {"Authorization": f"Bearer {token}"}

    return _factory


@pytest.fixture
def expired_auth_headers(app):
    def _factory(user_id: uuid.UUID) -> dict[str, str]:
        token = build_expired_token(user_id)
        return {"Authorization": f"Bearer {token}"}

    return _factory


@pytest.fixture
async def authed_client(app, auth_headers, test_user_id):
    headers = auth_headers(test_user_id)
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers=headers,
    ) as http_client:
        yield http_client


@pytest.fixture
def llm_quiz_output():
    return build_default_quiz_output()


@pytest.fixture
def mock_llm(monkeypatch, llm_quiz_output):
    import app.modules.llm.service as llm_service

    async def _fake_generate(self, generation_input):
        del generation_input
        return llm_quiz_output

    monkeypatch.setattr(llm_service.LLMService, "generate_quiz", _fake_generate)
    return llm_quiz_output
