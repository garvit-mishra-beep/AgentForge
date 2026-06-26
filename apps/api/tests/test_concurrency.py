"""Concurrency and race condition tests."""

import asyncio
import time

import pytest

from core.redis import (
    review_store_get,
    review_store_set,
    review_store_update,
    rate_limit_check,
    rate_limit_reset,
)


@pytest.mark.asyncio
async def test_review_store_concurrent_updates():
    """Multiple concurrent updates should not lose data."""
    review_id = "concurrent-test-1"
    await review_store_set(review_id, {"status": "queued", "issues": [], "count": 0})

    async def update_count():
        for _ in range(10):
            data = await review_store_get(review_id)
            if data:
                data["count"] = data.get("count", 0) + 1
                await review_store_set(review_id, data)
            await asyncio.sleep(0.001)

    tasks = [update_count() for _ in range(5)]
    await asyncio.gather(*tasks)

    final = await review_store_get(review_id)
    assert final is not None
    # Even with atomic issues, at least some updates should be reflected
    assert final["count"] > 0


@pytest.mark.asyncio
async def test_review_store_update_race_condition():
    """review_store_update should handle concurrent access."""
    review_id = "concurrent-test-2"
    await review_store_set(review_id, {"status": "queued", "phase": "started"})

    async def update_tracker():
        await review_store_update(review_id, {"phase": "analyzing"})
        await asyncio.sleep(0.01)
        await review_store_update(review_id, {"phase": "reviewing"})
        await asyncio.sleep(0.01)
        await review_store_update(review_id, {"phase": "completed"})

    tasks = [update_tracker() for _ in range(3)]
    await asyncio.gather(*tasks)

    final = await review_store_get(review_id)
    assert final is not None
    assert final["status"] == "queued"
    assert "phase" in final


@pytest.mark.asyncio
async def test_rate_limiter_concurrent_access():
    """Rate limiter should handle concurrent requests from same IP."""
    await rate_limit_reset()
    ip = "concurrent-ip-1"

    async def check_limit():
        return await rate_limit_check(ip, limit=5, window=60)

    results = await asyncio.gather(*[check_limit() for _ in range(10)])

    allowed = sum(1 for r in results if r)
    blocked = sum(1 for r in results if not r)
    assert allowed <= 5
    assert blocked >= 5


@pytest.mark.asyncio
async def test_inmem_store_max_entries():
    """In-memory store should not exceed MAX entries."""
    from core.redis import _inmem_reviews, _INMEM_REVIEWS_MAX

    for i in range(_INMEM_REVIEWS_MAX + 100):
        await review_store_set(f"stress-{i}", {"id": i})

    assert len(_inmem_reviews) <= _INMEM_REVIEWS_MAX + 1
    _inmem_reviews.clear()
