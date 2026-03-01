"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "SYP Learning Platform API"
    app_version: str = "0.1.0"
    debug: bool = False
    frontend_base_url: str = "http://localhost:3000"

    # Database
    database_url: str
    echo_sql: bool = False  # Set to True to log SQL queries

    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"  # Universal standard algorithm
    jwt_expiration_hours: int = 5  # App logic

    # Magic Link Configuration
    magic_link_expiration_minutes: int = 5  # App logic

    # Mail-Service Configuration
    SMTP_HOST: str
    SMTP_PORT: int = 587  # Standard port for STARTTLS
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM: str
    SMTP_USE_TLS: bool = True  # Secure default

    # LLM Configuration
    llm_provider: str

    llm_api_url: str
    llm_auth_user: str = ""  # Optional (BasicAuth), empty = no auth
    llm_auth_password: str = ""  # Optional (BasicAuth)
    llm_ollama_generation_model: str
    llm_ollama_utility_model: str

    # LiteLLM-specific (cloud providers)
    llm_litellm_generation_model: str
    llm_litellm_utility_model: str
    llm_openai_api_key: str = ""  # Optional
    llm_anthropic_api_key: str = ""  # Optional
    llm_google_api_key: str = ""  # Optional

    llm_timeout_seconds: float = 180.0  # App logic

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
