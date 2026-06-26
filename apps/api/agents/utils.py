import asyncio
import json
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from core.providers import AIProvider, AIProviderError, ChatResponse

logger = logging.getLogger(__name__)


async def call_with_retry(
    provider: AIProvider,
    model: str,
    system_prompt: str,
    user_message: str,
    retries: int = 2,
    max_tokens: int | None = None,
    timeout_s: float | None = None,
) -> ChatResponse:
    last_error: AIProviderError | None = None
    for attempt in range(retries + 1):
        try:
            coro = provider.chat(
                model, system_prompt, user_message,
                max_tokens=max_tokens, timeout_s=timeout_s,
            )
            if timeout_s is not None:
                return await asyncio.wait_for(coro, timeout=timeout_s)
            return await coro
        except TimeoutError:
            logger.warning("Provider call timed out (attempt %d/%d)", attempt + 1, retries + 1)
            raise
        except AIProviderError as e:
            last_error = e
            logger.warning("Provider call failed (attempt %d/%d): %s", attempt + 1, retries + 1, e)
            if attempt < retries:
                wait = 2**attempt
                logger.info("Retrying in %ds...", wait)
                await asyncio.sleep(wait)
    raise last_error


def _is_timeout(result: ChatResponse) -> bool:
    return getattr(result, "_timed_out", False)


async def call_with_timeout(
    provider: AIProvider,
    model: str,
    system_prompt: str,
    user_message: str,
    timeout_s: float = 30.0,
    max_tokens: int | None = None,
) -> ChatResponse:
    try:
        return await call_with_retry(
            provider, model, system_prompt, user_message,
            retries=0, max_tokens=max_tokens, timeout_s=timeout_s,
        )
    except TimeoutError:
        logger.warning("Agent timed out after %ss, returning partial result", timeout_s)
        result = ChatResponse(
            content="",
            token_usage=None,
            duration_ms=timeout_s * 1000,
            model=model,
        )
        result._timed_out = True
        return result


def parse_json_output(text: str) -> dict | None:
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        logger.warning("Could not parse JSON from agent output")
        return None


_PROMPT_ENV: Environment | None = None


def _get_prompt_env() -> Environment:
    global _PROMPT_ENV
    if _PROMPT_ENV is None:
        prompt_dir = Path(__file__).parent / "prompts"
        _PROMPT_ENV = Environment(loader=FileSystemLoader(str(prompt_dir)))
    return _PROMPT_ENV


def load_prompt_template(template_name: str) -> Environment:
    return _get_prompt_env()
