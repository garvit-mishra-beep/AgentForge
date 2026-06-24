from __future__ import annotations

import os
import sys
from functools import lru_cache
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APPLICATION_NAME: str = "AgentForge AI"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql+asyncpg://agentforge:agentforge@localhost:5432/agentforge"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_DB: int = 0

    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None

    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_AUDIENCE: str = "agentforge-api"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OPEN_SOURCE_BASE_URL: Optional[str] = None
    OPEN_SOURCE_MODEL: Optional[str] = None

    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    LOG_LEVEL: str = "INFO"
    ENABLE_TRACING: bool = False
    ENABLE_METRICS: bool = True
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    ENABLE_JSON_LOGS: bool = False

    LLM_TIMEOUT_SECONDS: int = 60
    QDRANT_TIMEOUT_SECONDS: int = 30
    REDIS_TIMEOUT_SECONDS: int = 5

    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60

    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB

    ALLOWED_UPLOAD_MIME_TYPES: List[str] = [
        "application/pdf",
        "text/plain",
        "text/markdown",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


def validate_settings(s: Settings) -> None:
    if not s.JWT_SECRET or s.JWT_SECRET.strip() == "":
        print("FATAL: JWT_SECRET is not set. Set JWT_SECRET in your .env file.", file=sys.stderr)
        sys.exit(1)
    DEFAULT_JWT_SECRETS = ["change-this-in-production", "local-dev-secret-change-me", "change-this-to-a-random-secret-in-production"]
    if s.JWT_SECRET in DEFAULT_JWT_SECRETS:
        print(f"FATAL: JWT_SECRET is still set to a default value. Generate a secure random secret with: openssl rand -hex 32", file=sys.stderr)
        sys.exit(1)


@lru_cache()
def get_settings() -> Settings:
    s = Settings()
    validate_settings(s)
    return s


settings = get_settings()
