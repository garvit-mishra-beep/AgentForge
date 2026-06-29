import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.routes.keys import get_user_api_key
from core.config import settings


def _retry_exception(exception) -> bool:
    if isinstance(exception, (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.PoolTimeout)):
        return True
    if isinstance(exception, httpx.HTTPStatusError):
        # Retry on 429 (rate limit) and 5xx (server errors)
        return exception.response.status_code == 429 or 500 <= exception.response.status_code < 600
    # Support library-specific exceptions (e.g. OpenAI/Anthropic APIStatusError)
    status_code = getattr(exception, "status_code", None)
    if status_code is not None:
        return status_code == 429 or 500 <= status_code < 600
    return False

logger = logging.getLogger(__name__)

# â”€â”€ Dataclasses and Exceptions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@dataclass
class ChatResponse:
    content: str
    token_usage: dict | None = None
    duration_ms: float | None = None
    model: str = ""


class AIProviderError(Exception):
    def __init__(self, provider: str, model: str, message: str):
        self.provider = provider
        self.model = model
        super().__init__(f"[{provider}:{model}] {message}")


class ConfigurationError(ValueError):
    pass


@dataclass
class ProviderConfig:
    api_key: str
    base_url: str | None = None
    organization: str | None = None


class AIProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        model: str,
        system_prompt: str,
        user_message: str,
        max_tokens: int | None = None,
        timeout_s: float | None = None,
    ) -> ChatResponse:
        ...


# â”€â”€ Shared HTTP client pool â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_shared_client: httpx.AsyncClient | None = None


def _get_client(timeout: float = 300.0) -> httpx.AsyncClient:
    global _shared_client
    if _shared_client is None:
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
        _shared_client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=limits,
        )
    return _shared_client


async def close_shared_client() -> None:
    global _shared_client
    if _shared_client:
        await _shared_client.aclose()
        _shared_client = None


# â”€â”€ OpenAI â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class OpenAIProvider(AIProvider):
    def __init__(self, config: ProviderConfig | None = None):
        self.config = config
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            http_client = _get_client()
            api_key = self.config.api_key if self.config else settings.openai_api_key
            base_url = (self.config.base_url if self.config else None) or "https://api.openai.com/v1"
            org = self.config.organization if self.config else None
            self._client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
                organization=org,
                http_client=http_client,
            )
        return self._client

    async def chat(
        self,
        model: str,
        system_prompt: str,
        user_message: str,
        max_tokens: int | None = None,
        timeout_s: float | None = None,
    ) -> ChatResponse:
        client = await self._get_client()
        start = time.monotonic()
        try:
            kwargs = dict(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.2,
            )
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
            if timeout_s is not None:
                kwargs["timeout"] = timeout_s
            response = await self._make_retryable_api_call(client, kwargs)
            duration_ms = (time.monotonic() - start) * 1000
            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            return ChatResponse(
                content=response.choices[0].message.content or "",
                token_usage=usage,
                duration_ms=duration_ms,
                model=model,
            )
        except Exception as e:
            raise AIProviderError("openai", model, str(e)) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(_retry_exception),
        reraise=True
    )
    async def _make_retryable_api_call(self, client, kwargs):
        return await client.chat.completions.create(**kwargs)


# â”€â”€ Anthropic â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class AnthropicProvider(AIProvider):
    def __init__(self, config: ProviderConfig | None = None):
        self.config = config
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from anthropic import AsyncAnthropic
            api_key = self.config.api_key if self.config else settings.anthropic_api_key
            base_url = self.config.base_url if self.config else None
            self._client = AsyncAnthropic(
                api_key=api_key,
                base_url=base_url,
                http_client=_get_client(),
            )
        return self._client

    async def chat(
        self,
        model: str,
        system_prompt: str,
        user_message: str,
        max_tokens: int | None = None,
        timeout_s: float | None = None,
    ) -> ChatResponse:
        client = await self._get_client()
        start = time.monotonic()
        try:
            kwargs = dict(
                model=model,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                max_tokens=max_tokens or 512,
                temperature=0.2,
            )
            if timeout_s is not None:
                kwargs["timeout"] = timeout_s
            response = await self._make_retryable_api_call(client, kwargs)
            duration_ms = (time.monotonic() - start) * 1000
            usage = None
            if hasattr(response, "usage"):
                usage = {
                    "prompt_tokens": getattr(response.usage, "input_tokens", 0),
                    "completion_tokens": getattr(response.usage, "output_tokens", 0),
                    "total_tokens": getattr(response.usage, "input_tokens", 0) + getattr(response.usage, "output_tokens", 0),
                }
            return ChatResponse(
                content=response.content[0].text,
                token_usage=usage,
                duration_ms=duration_ms,
                model=model,
            )
        except Exception as e:
            raise AIProviderError("anthropic", model, str(e)) from e


    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(_retry_exception),
        reraise=True
    )
    async def _make_retryable_api_call(self, client, kwargs):
        return await client.messages.create(**kwargs)


# â”€â”€ Google â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class GoogleProvider(AIProvider):
    def __init__(self, config: ProviderConfig | None = None):
        self.config = config
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from google import genai
            api_key = self.config.api_key if self.config else settings.google_api_key
            self._client = genai.Client(api_key=api_key)
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(_retry_exception),
        reraise=True
    )
    async def _make_retryable_api_call(self, client, kwargs):
        return await client.aio.models.generate_content(
            model=kwargs["model"],
            contents=kwargs["contents"],
            config=type(
                "Config",
                (),
                {
                    "system_instruction": kwargs.get("system_instruction"),
                    "temperature": kwargs.get("temperature", 0.2),
                    **({"max_output_tokens": kwargs["max_output_tokens"]} if "max_output_tokens" in kwargs else {}),
                },
            )(),
        )


    async def chat(
        self,
        model: str,
        system_prompt: str,
        user_message: str,
        max_tokens: int | None = None,
        timeout_s: float | None = None,
    ) -> ChatResponse:
        client = await self._get_client()
        start = time.monotonic()
        try:
            kwargs = dict(
                model=model,
                contents=user_message,
                system_instruction=system_prompt,
                temperature=0.2,
            )
            if max_tokens is not None:
                kwargs["max_output_tokens"] = max_tokens
            response = await self._make_retryable_api_call(client, kwargs)
            duration_ms = (time.monotonic() - start) * 1000
            usage = None
            if hasattr(response, "usage_metadata"):
                usage = {
                    "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                    "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
                    "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
                }
            return ChatResponse(
                content=response.text,
                token_usage=usage,
                duration_ms=duration_ms,
                model=model,
            )
        except Exception as e:
            raise AIProviderError("google", model, str(e)) from e





# â”€â”€ OpenAI Compatible (Groq, OpenRouter, etc.) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class OpenAICompatibleProvider(AIProvider):
    def __init__(self, config: ProviderConfig | None = None):
        self.config = config
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            http_client = _get_client()
            api_key = self.config.api_key if self.config else settings.openai_api_key
            base_url = self.config.base_url if self.config else None
            self._client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
                http_client=http_client,
            )
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(_retry_exception),
        reraise=True
    )
    async def _make_retryable_api_call(self, client, kwargs):
        return await client.chat.completions.create(**kwargs)

    async def chat(
        self,
        model: str,
        system_prompt: str,
        user_message: str,
        max_tokens: int | None = None,
        timeout_s: float | None = None,
    ) -> ChatResponse:
        client = await self._get_client()
        start = time.monotonic()
        try:
            kwargs = dict(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.2,
            )
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
            if timeout_s is not None:
                kwargs["timeout"] = timeout_s
            response = await self._make_retryable_api_call(client, kwargs)
            duration_ms = (time.monotonic() - start) * 1000
            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            return ChatResponse(
                content=response.choices[0].message.content or "",
                token_usage=usage,
                duration_ms=duration_ms,
                model=model,
            )
        except Exception as e:
            raise AIProviderError("openai-compatible", model, str(e)) from e


# â”€â”€ Factories and Resolvers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def create_provider(provider_type: str, config: ProviderConfig | None = None) -> AIProvider:
    """Create a provider instance based on type and configuration."""
    if provider_type == "openai":
        return OpenAIProvider(config)
    elif provider_type == "anthropic":
        return AnthropicProvider(config)
    elif provider_type == "google":
        return GoogleProvider(config)
    elif provider_type in ["openrouter", "groq", "openai-compatible"]:
        return OpenAICompatibleProvider(config)
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")


def get_provider_from_model(model: str) -> str:
    """Determine provider type from model name."""
    model_lower = model.lower()

    if model_lower.startswith("openai/") or any(keyword in model_lower for keyword in ["gpt-", "text-embedding"]) or model_lower in ["gpt-4", "gpt-3.5-turbo"]:
        return "openai"
    elif model_lower.startswith("anthropic/") or "claude-" in model_lower:
        return "anthropic"
    elif model_lower.startswith("google/") or "gemini-" in model_lower or "palm-" in model_lower:
        return "google"

    elif any(provider in model_lower for provider in ["openrouter", "groq"]):
        if "openrouter" in model_lower:
            return "openrouter"
        elif "groq" in model_lower:
            return "groq"
    elif "/" in model_lower:
        # Handle format like "provider/model-name"
        provider_part = model_lower.split("/")[0]
        if provider_part in ["openai", "anthropic", "google", "openrouter", "groq"]:
            return provider_part

    # Default fallback
    return "unknown"


async def get_provider_for_user(
    model: str,
    user_id: str,
    project_id: str | None = None,
    db: Any = None
) -> tuple[AIProvider, str]:
    """
    Get a provider instance for a specific user and project.
    Returns (provider_instance, provider_type) tuple.
    """
    if db is None:
        raise ValueError("Database session is required for BYOK provider resolution")

    # Determine the provider type from the model name
    provider_type = get_provider_from_model(model)

    # Try to get user's API key for this provider/project
    key_info = await get_user_api_key(db, user_id, provider_type, project_id)

    # If no key found, try without project-specific (fallback to user-level)
    if not key_info and project_id is not None:
        key_info = await get_user_api_key(db, user_id, provider_type, None)

    # If still no key, check if there are global settings as fallback
    if not key_info:
        if provider_type == "openai" and settings.openai_api_key:
            config = ProviderConfig(api_key=settings.openai_api_key)
            return create_provider(provider_type, config), provider_type
        elif provider_type == "anthropic" and settings.anthropic_api_key:
            config = ProviderConfig(api_key=settings.anthropic_api_key)
            return create_provider(provider_type, config), provider_type
        elif provider_type == "google" and settings.google_api_key:
            config = ProviderConfig(api_key=settings.google_api_key)
            return create_provider(provider_type, config), provider_type
        raise ConfigurationError(
            "No provider configured for this model."
        )

    # Get endpoint configuration if available
    endpoint_config = await get_user_endpoint_config(
        db, user_id, provider_type, project_id
    )

    # Build provider configuration
    config = ProviderConfig(
        api_key=key_info["key"],
        base_url=endpoint_config.get("base_url") if endpoint_config else None,
        organization=endpoint_config.get("organization") if endpoint_config else None,
    )

    return create_provider(provider_type, config), provider_type


async def get_user_endpoint_config(
    db: Any,
    user_id: str,
    provider: str,
    project_id: str | None
) -> dict | None:
    """Get endpoint configuration for user/provider/project."""
    query = """
        SELECT base_url, api_key_id, headers, config
        FROM api_endpoints
        WHERE user_id = $1 AND provider = $2 AND is_enabled = true
    """
    params = [user_id, provider]
    param_idx = 3

    if project_id is not None:
        query += f" AND project_id = ${param_idx}"
        params.append(project_id)
        param_idx += 1
    else:
        query += " AND project_id IS NULL"

    # Prefer default endpoint, then most recently updated
    query += " ORDER BY is_default DESC, updated_at DESC LIMIT 1"

    row = await db.fetchrow(query, *params)
    if not row:
        return None

    return {
        "base_url": row["base_url"],
        "headers": row["headers"] or {},
        "config": row["config"] or {},
    }


# Helper functions for checking if this is the first key/endpoint
async def _is_first_key_for_user_provider(
    db: Any, user_id: str, provider: str, project_id: str | None
) -> bool:
    """Check if this is the first key for user/provider/project."""
    query = """
        SELECT COUNT(*) as count
        FROM api_keys
        WHERE user_id = $1 AND provider = $2 AND is_enabled = true
    """
    params = [user_id, provider]

    if project_id is not None:
        query += " AND project_id = $3"
        params.append(project_id)
    else:
        query += " AND project_id IS NULL"

    result = await db.fetchrow(query, *params)
    return result["count"] == 0


async def _is_first_endpoint_for_user_provider(
    db: Any, user_id: str, provider: str, project_id: str | None
) -> bool:
    """Check if this is the first endpoint for user/provider/project."""
    query = """
        SELECT COUNT(*) as count
        FROM api_endpoints
        WHERE user_id = $1 AND provider = $2 AND is_enabled = true
    """
    params = [user_id, provider]

    if project_id is not None:
        query += " AND project_id = $3"
        params.append(project_id)
    else:
        query += " AND project_id IS NULL"

    result = await db.fetchrow(query, *params)
    return result["count"] == 0


def get_provider(model: str) -> AIProvider:
    """
    Backward compatibility function that returns a provider based on global settings.
    """
    # Determine provider type from model name
    provider_type = get_provider_from_model(model)

    # Fall back to global settings, using placeholder keys if not configured to allow object inspection/instantiation in tests
    if provider_type == "openai":
        config = ProviderConfig(api_key=settings.openai_api_key or "sk-dummy")
        return create_provider(provider_type, config)
    elif provider_type == "anthropic":
        config = ProviderConfig(api_key=settings.anthropic_api_key or "sk-ant-dummy")
        return create_provider(provider_type, config)
    elif provider_type == "google":
        config = ProviderConfig(api_key=settings.google_api_key or "AIza-dummy")
        return create_provider(provider_type, config)
    elif provider_type in ["openrouter", "groq", "openai-compatible"]:
        config = ProviderConfig(api_key=settings.openai_api_key or "sk-dummy")
        return create_provider(provider_type, config)
    else:
        raise ValueError(f"Unknown model provider: {model}")
