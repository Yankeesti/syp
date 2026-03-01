# Quiz-App

AI-powered quiz application consisting of a React frontend, a FastAPI backend, and a PostgreSQL database. All services run as Docker containers.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (including Docker Compose)
- Linux system (Ubuntu/Debian, Fedora, Arch) or manually installed Docker on macOS/Windows

---

## Quick Start (recommended)

The installer automatically handles: Docker installation, repository clone, `.env` setup, and starting all services.

```bash
curl -fsSL https://raw.githubusercontent.com/Yankeesti/syp/refs/heads/master/install.sh | bash
```

You will be prompted for the path to your `.env` file. Use `.env.example` in the repo root as a reference.

---

## Configuration (`.env`)

| Variable | Description |
|----------|-------------|
| `FRONTEND_BASE_URL` | Public URL of the frontend – used by the backend for magic link URLs in emails |
| `VITE_API_BASE_URL` | Public URL of the backend – used by the frontend for all API requests |
| `DB_USER` | Username for the PostgreSQL database |
| `DB_PASSWORD` | Password for the PostgreSQL database |
| `DB_NAME` | Name of the PostgreSQL database |
| `JWT_SECRET_KEY` | Secret key for signing JWT tokens – generate randomly, e.g. `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `JWT_EXPIRATION_HOURS` | Validity duration of a JWT token in hours (default: `5`) |
| `MAGIC_LINK_EXPIRATION_MINUTES` | Validity duration of a magic link for passwordless login in minutes (default: `5`) |
| `SMTP_*` | SMTP credentials for sending emails (magic links) |
| `LLM_PROVIDER` | Specifies which LLM provider to use: `ollama` for local/self-hosted models, `litellm` for cloud providers (OpenAI, Anthropic, Google) |
| `LLM_API_URL` | API endpoint of the Ollama server (only relevant when `LLM_PROVIDER=ollama`) |
| `LLM_AUTH_USER` / `LLM_AUTH_PASSWORD` | HTTP BasicAuth credentials for the Ollama server, if it is secured |
| `LLM_OLLAMA_GENERATION_MODEL` | Ollama model for quiz generation (e.g. `deepseek-r1:32b`) |
| `LLM_OLLAMA_UTILITY_MODEL` | Ollama model for utility tasks such as validation (e.g. `qwen2.5:14b`) |
| `LLM_LITELLM_GENERATION_MODEL` | Cloud model for quiz generation when `LLM_PROVIDER=litellm` (e.g. `gpt-4o`) |
| `LLM_LITELLM_UTILITY_MODEL` | Cloud model for utility tasks when `LLM_PROVIDER=litellm` (e.g. `gpt-4o-mini`) |
| `LLM_OPENAI_API_KEY` | API key for OpenAI (only when `LLM_PROVIDER=litellm`) |
| `LLM_ANTHROPIC_API_KEY` | API key for Anthropic (only when `LLM_PROVIDER=litellm`) |
| `LLM_GOOGLE_API_KEY` | API key for Google (only when `LLM_PROVIDER=litellm`) |
| `LLM_TIMEOUT_SECONDS` | Maximum wait time for an LLM response in seconds (default: `180`) |
