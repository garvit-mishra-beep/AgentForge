from __future__ import annotations

import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


class LLMProvider:
    async def generate(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096) -> dict:
        raise NotImplementedError

    async def generate_stream(self, messages: list[dict], temperature: float = 0.7):
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key

    async def generate(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096) -> dict:
        if not self.api_key:
            return {"content": f"[Mock] Response to: {messages[-1].get('content', '')[:50]}...", "tokens_in": 50, "tokens_out": 30}
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key)
        response = await client.chat.completions.create(
            model=self.model, messages=messages, temperature=temperature, max_tokens=max_tokens
        )
        choice = response.choices[0]
        return {
            "content": choice.message.content or "",
            "tokens_in": response.usage.prompt_tokens if response.usage else 0,
            "tokens_out": response.usage.completion_tokens if response.usage else 0,
        }


class AnthropicProvider(LLMProvider):
    def __init__(self, model: str = "claude-3-5-sonnet-20240620", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key

    async def generate(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096) -> dict:
        if not self.api_key:
            return {"content": f"[Mock] Response to: {messages[-1].get('content', '')[:50]}...", "tokens_in": 50, "tokens_out": 30}
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=self.api_key)
        system = None
        chat_messages = messages
        if messages and messages[0].get("role") == "system":
            system = messages[0]["content"]
            chat_messages = messages[1:]
        response = await client.messages.create(
            model=self.model, messages=chat_messages, system=system, max_tokens=max_tokens, temperature=temperature
        )
        return {
            "content": response.content[0].text if response.content else "",
            "tokens_in": response.usage.input_tokens if response.usage else 0,
            "tokens_out": response.usage.output_tokens if response.usage else 0,
        }


def get_llm(provider: str = "openai", model: Optional[str] = None, api_key: Optional[str] = None) -> LLMProvider:
    if provider == "openai":
        return OpenAIProvider(model=model or "gpt-4o", api_key=api_key)
    elif provider == "anthropic":
        return AnthropicProvider(model=model or "claude-3-5-sonnet-20240620", api_key=api_key)
    elif provider == "gemini":
        return OpenAIProvider(model=model or "gemini-1.5-flash", api_key=api_key)
    else:
        return OpenAIProvider(model=model or "gpt-4o", api_key=api_key)
