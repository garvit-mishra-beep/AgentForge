import logging

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    database_url: str = ""
    database_pool_min: int = 2
    database_pool_max: int = 10

    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    redis_url: str = "redis://localhost:6379/0"



    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    openrouter_api_key: str = ""
    groq_api_key: str = ""

    encryption_key: str = ""

    # JWT auth
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    jwt_refresh_secret: str = ""
    jwt_refresh_expire_days: int = 7
    cookie_secure: bool = False
    frontend_url: str = "http://localhost:3000"

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""


    max_steps: int = 20
    task_timeout_minutes: int = 10

    fast_demo_mode: bool = False
    max_retries: int = 2
    max_output_tokens: int = 2048
    max_context_messages: int = 20
    max_execution_time: int = 600
    agent_timeout_lead: int = 20
    agent_timeout_builder: int = 30
    agent_timeout_reviewer: int = 15
    agent_timeout_deliver: int = 15

    review_rate_limit: int = 10
    review_rate_window: int = 3600
    review_max_code_length: int = 50000
    review_max_concurrent: int = 4
    review_queue_maxsize: int = 20
    review_models_baseline: str = "gpt-4o-mini,claude-haiku-3-5,gemini-2.0-flash"
    review_models_builder: str = "gpt-4o-mini,claude-haiku-3-5,gemini-2.0-flash"
    review_models_reviewer: str = "gpt-4o-mini,claude-haiku-3-5,gemini-2.0-flash"

    auth_enabled: bool = True
    log_level: str = "INFO"

    # GitHub App integration (PR review bot)
    github_app_id: str = ""
    github_app_private_key: str = ""  # PEM contents OR a file path
    github_webhook_secret: str = ""
    github_api_base: str = "https://api.github.com"
    github_review_model: str = "gpt-4o-mini"
    log_format: str = "text"

    upload_dir: str = "uploads"
    max_upload_size: int = 100 * 1024 * 1024  # 100 MB

    rate_limit_per_minute: int = 60
    rate_limit_auth_per_minute: int = 10
    brute_force_max_attempts: int = 5
    brute_force_lockout_seconds: int = 900

    allowed_upload_mime_types: list[str] = [
        "text/plain", "text/x-python", "text/x-java", "text/x-c",
        "text/x-c++", "text/x-javascript", "text/x-typescript",
        "text/html", "text/css", "text/markdown",
        "application/json", "application/xml", "application/x-yaml",
        "application/octet-stream",
        "image/png", "image/jpeg", "image/gif", "image/svg+xml",
    ]

    model_config = {"env_prefix": "AGENTFORGE_", "env_file": ".env"}

    @property
    def agent_timeout(self) -> dict[str, int]:
        return {
            "team_lead_plan": self.agent_timeout_lead,
            "builder": self.agent_timeout_builder,
            "reviewer": self.agent_timeout_reviewer,
            "team_lead_deliver": self.agent_timeout_deliver,
        }

    def validate(self) -> None:  # type: ignore
        errors: list[str] = []
        if not self.database_url:
            errors.append("AGENTFORGE_DATABASE_URL is required")
        if self.auth_enabled:
            if not self.jwt_secret:
                errors.append("AGENTFORGE_JWT_SECRET is required when auth_enabled=True")
            if len(self.jwt_secret) < 16:
                errors.append("AGENTFORGE_JWT_SECRET must be at least 16 characters")
            # A distinct refresh secret is mandatory: falling back to the access
            # secret would let an access token be replayed as a refresh token
            # (TOP_FINDINGS #7).
            if not self.jwt_refresh_secret:
                errors.append(
                    "AGENTFORGE_JWT_REFRESH_SECRET is required when auth_enabled=True"
                )
            elif len(self.jwt_refresh_secret) < 16:
                errors.append("AGENTFORGE_JWT_REFRESH_SECRET must be at least 16 characters")
            elif self.jwt_refresh_secret == self.jwt_secret:
                errors.append(
                    "AGENTFORGE_JWT_REFRESH_SECRET must differ from AGENTFORGE_JWT_SECRET"
                )
        if not self.fast_demo_mode:
            if not self.encryption_key:
                logger.warning(
                    "AGENTFORGE_ENCRYPTION_KEY not set. "
                    "Encrypted API keys will be unrecoverable after restart."
                )
        if self.review_rate_limit < 1:
            errors.append("AGENTFORGE_REVIEW_RATE_LIMIT must be >= 1")

        if errors:
            raise ValueError(
                "Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
            )


settings = Settings()
