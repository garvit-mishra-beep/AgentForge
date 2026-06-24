from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, TypeVar

import tenacity
from tenacity import retry as tenacity_retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import pybreaker

from apps.api.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")

LLM_TIMEOUT = 60.0
QDRANT_TIMEOUT = 30.0
REDIS_TIMEOUT = 5.0

llm_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)
qdrant_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=30)
redis_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=30)

llm_retry = tenacity_retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, asyncio.TimeoutError)),
    before_sleep=lambda retry_state: logger.warning(
        "LLM call failed (attempt %d/3), retrying...", retry_state.attempt_number
    ),
)

qdrant_retry = tenacity_retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=lambda retry_state: logger.warning(
        "Qdrant call failed (attempt %d/2), retrying...", retry_state.attempt_number
    ),
)

redis_retry = tenacity_retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=3),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=lambda retry_state: logger.warning(
        "Redis call failed (attempt %d/2), retrying...", retry_state.attempt_number
    ),
)


async def call_with_timeout(coro, timeout: float, service: str = "unknown") -> Any:
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.error("%s call timed out after %ds", service, timeout)
        raise TimeoutError(f"{service} timed out after {timeout}s")
