"""
Centralized configuration for AgentOS API.

Uses Pydantic settings for type-safe, environment-based configuration.
"""

import os
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables from .env files
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
load_dotenv()

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables take precedence over defaults.
    """

    # ===============================
    # APPLICATION
    # ===============================

    APPLICATION_NAME: str = "AgentOS"
    ENVIRONMENT: str = "development"  # development, staging, production

    # ===============================
    # SERVER
    # ===============================

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    TIMEOUT: int = 300  # seconds

    # ===============================
    # DATABASE
    # ===============================

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/agents"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_PREPARE: bool = True

    # ===============================
    # REDIS
    # ===============================

    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_DB: int = 0
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: float = 5.0
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_RETRY_BACKOFF: float = 0.3
    REDIS_RETRY_MAX_ATTEMPTS: int = 3

    # ===============================
    # JWT
    # ===============================

    JWT_SECRET: str = os.environ.get("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ===============================
    # AUTH
    # ===============================

    HASH_ALGORITHM: str = "pbkdf2_sha512"
    PBKDF2_ITERATIONS: int = 600000
    PBKDF2_SALT_LENGTH: int = 16

    # ===============================
    # CORS
    # ===============================

    CORS_ORIGINS: list = ["http://localhost:3000"]

    # ===============================
    # LOGGING
    # ===============================

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json, text, structlog
    LOG_COLORS: bool = True
    LOG_REQUEST_TIMEOUT: float = 30.0

    # ===============================
    # TELEMETRY
    # ===============================

    ENABLE_TRACING: bool = False
    TRACING_ENDPOINT: str = "http://localhost:4317/v1/traces"
    TRACING_SAMPLE_RATE: float = 1.0
    ENABLE_METRICS: bool = False
    METRICS_ENDPOINT: str = "http://localhost:9464/metrics"

    # ===============================
    # WEBSOCKET
    # ===============================

    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30  # seconds
    WEBSOCKET_PING_TIMEOUT: int = 10  # seconds
    WEBSOCKET_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    WEBSOCKET_QUEUE_SIZE: int = 1000

    # ===============================
    # WORKFLOWS
    # ===============================

    WORKFLOW_TIMEOUT_SECONDS: int = 3600
    WORKFLOW_MAX_RETRIES: int = 3
    WORKFLOW_RETRY_BACKOFF: float = 2.0
    WORKFLOW_CHECKPOINT_INTERVAL: int = 60  # seconds

    # ===============================
    # LLM CONFIGURATION
    # ===============================

    LLM_PROVIDER: str = "gemini"  # gemini, openai, anthropic, open-source
    GEMINI_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    OPEN_SOURCE_API_KEY: str | None = None
    OPEN_SOURCE_BASE_URL: str = "http://localhost:11434/v1"
    OPEN_SOURCE_MODEL: str = "llama3"

    PLANNER_PROVIDER: str = "gemini"
    DEVELOPER_PROVIDER: str = "openai"
    TESTER_PROVIDER: str = "openai"
    REVIEWER_PROVIDER: str = "anthropic"

    # ===============================
    # SECURITY
    # ===============================

    ALLOWED_HOSTS: list = ["*"]
    TRUSTED_PROXIES: list = []

    # ===============================
    # RATE LIMITING
    # ===============================

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    RATE_LIMIT_BURST: int = 20

    @property
    def database_url(self) -> str:
        """Get database URL with pool settings."""
        return f"{self.DATABASE_URL}?pool_size={self.DATABASE_POOL_SIZE}&max_overflow={self.DATABASE_MAX_OVERFLOW}&pool_timeout={self.DATABASE_POOL_TIMEOUT}"

    @property
    def redis_pool(self) -> str:
        """Get Redis pool URL."""
        return f"{self.REDIS_URL}?db={self.REDIS_DB}&max_connections={self.REDIS_MAX_CONNECTIONS}"

    def cors_origins_set(self) -> set:
        """Get CORS origins as set for membership testing."""
        return set(o.strip() for o in self.CORS_ORIGINS if o.strip())


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Loaded and cached settings
    """
    return Settings()


# Export settings for use
settings = get_settings()
