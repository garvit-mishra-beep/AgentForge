import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from core.config import settings

logger = logging.getLogger(__name__)


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


# ── Shared HTTP client pool ────────────────────────────────────────────

import httpx

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


# ── OpenAI ─────────────────────────────────────────────────────────────

class OpenAIProvider(AIProvider):
    def __init__(self):
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            http_client = _get_client()
            self._client = AsyncOpenAI(
                api_key=settings.openai_api_key,
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
            response = await client.chat.completions.create(**kwargs)
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


# ── Anthropic ──────────────────────────────────────────────────────────

class AnthropicProvider(AIProvider):
    def __init__(self):
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(
                api_key=settings.anthropic_api_key,
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
            response = await client.messages.create(**kwargs)
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


# ── Google ─────────────────────────────────────────────────────────────

class GoogleProvider(AIProvider):
    def __init__(self):
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=settings.google_api_key)
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
            config_kwargs = dict(
                system_instruction=system_prompt,
                temperature=0.2,
            )
            if max_tokens is not None:
                config_kwargs["max_output_tokens"] = max_tokens
            response = await client.aio.models.generate_content(
                model=model,
                contents=user_message,
                config=type(
                    "Config",
                    (),
                    {"system_instruction": system_prompt, "temperature": 0.2, **({"max_output_tokens": max_tokens} if max_tokens else {})},
                )(),
            )
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


# ── Ollama ─────────────────────────────────────────────────────────────

class OllamaProvider(AIProvider):
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")

    async def chat(
        self,
        model: str,
        system_prompt: str,
        user_message: str,
        max_tokens: int | None = None,
        timeout_s: float | None = None,
    ) -> ChatResponse:
        options = {"temperature": 0.2}
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": options,
        }
        start = time.monotonic()
        try:
            client = _get_client(timeout=timeout_s or 300.0)
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            duration_ms = (time.monotonic() - start) * 1000

            content = data.get("message", {}).get("content", "")

            usage = None
            eval_count = data.get("eval_count")
            prompt_eval_count = data.get("prompt_eval_count")
            if eval_count is not None or prompt_eval_count is not None:
                usage = {
                    "prompt_tokens": prompt_eval_count or 0,
                    "completion_tokens": eval_count or 0,
                    "total_tokens": (prompt_eval_count or 0) + (eval_count or 0),
                }

            return ChatResponse(
                content=content,
                token_usage=usage,
                duration_ms=duration_ms,
                model=model,
            )
        except Exception as e:
            raise AIProviderError("ollama", model, str(e)) from e


# ── Provider resolution ────────────────────────────────────────────────

OLLAMA_MODEL_KEYWORDS = {
    "llama", "qwen", "deepseek", "gemma", "mistral", "phi",
    "dolphin", "mixtral", "codellama", "neural", "orca",
    "yi", "falcon", "starling", "openhermes", "zephyr",
    "tinylama", "tinyllama", "llava", "bakllava",
    "nous-hermes", "solar", "openchat", "starcoder",
    "wizardcoder", "phind", "magicoder",
}


def get_provider(model: str) -> AIProvider:
    model_lower = model.lower()
    if any(keyword in model_lower for keyword in ("gpt", "openai")):
        return OpenAIProvider()
    elif any(keyword in model_lower for keyword in ("claude", "anthropic")):
        return AnthropicProvider()
    elif any(keyword in model_lower for keyword in ("gemini", "google")):
        return GoogleProvider()
    elif (
        any(keyword in model_lower for keyword in ("ollama",))
        or "/" in model
        or any(kw in model_lower for kw in OLLAMA_MODEL_KEYWORDS)
    ):
        return OllamaProvider()
    else:
        raise ValueError(f"Unknown model provider: {model}")
