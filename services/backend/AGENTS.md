# Repository Guidelines

## Project Structure & Module Organization
- Source: `app/`
  - `app/main.py` – FastAPI entrypoint; run with Uvicorn.
  - `app/core/` – config, DB session, security, exceptions.
  - `app/shared/` – common dependencies and utils.
  - `app/modules/` – domain modules (`auth`, `quiz`, `learning`, `llm`) with layered folders: `router.py`, `services/`, `repositories/`, `models/`, `schemas/`.
  - `app/alembic/` – Alembic config and `versions/` migrations.
- Tests: `tests/` (see `pytest` config in `pyproject.toml`).
- Tooling: `pyproject.toml` (deps, pytest, black), `.pre-commit-config.yaml`.

## Build, Test, and Development Commands
- Install deps: `poetry install`
- Run dev server: `poetry run uvicorn app.main:app --reload`
- Tests + coverage: `poetry run pytest`
- Format code: `poetry run poe format`
- Alembic (examples):
  - Generate: `poetry run alembic revision --autogenerate -m "msg"`
  - Migrate: `poetry run alembic upgrade head`

## Coding Style & Naming Conventions
- Python 3.13+, 4‑space indentation, max line length 88 (Black).
- Use type hints everywhere; prefer explicit return types in services/repositories.
- Names: `snake_case` for modules/functions/vars, `PascalCase` for classes, `CONSTANT_CASE` for constants.
- Module layout: keep API in `router.py`, business rules in `services/`, data access in `repositories/`; no cross‑layer leaks.
- Run `poetry run poe format` before committing (or enable pre‑commit).

## Testing Guidelines
- Framework: `pytest` with `pytest-asyncio` and coverage.
- Structure: mirror app modules under `tests/unit/<module>/`.
- Naming: files `test_*.py`, classes `Test*`, functions `test_*` (configured in `pyproject.toml`).
- Use in‑memory SQLite fixtures (see `tests/conftest.py`); avoid network/DB side effects.

## Commit & Pull Request Guidelines
- Commit style: prefer Conventional Commits, e.g. `refactor(quiz): extract update logic` (matches history).
- Keep commits focused; include rationale in the body when non‑trivial.
- PRs must include:
  - Summary, scope, and module(s) touched.
  - Linked issue (if applicable) and migration notes (if Alembic changes).
  - Test coverage evidence (CI or `htmlcov/`), and local run commands.

## Security & Configuration Tips
- Copy envs: `cp .env.example .env`. Do not commit secrets.
- Use `postgresql+asyncpg://` for `DATABASE_URL` (async SQLAlchemy).
- For new models: import them in `app/models/__init__.py` so Alembic detects changes.

