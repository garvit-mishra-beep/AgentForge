"""Redis client wrapper with automatic fallback to in-memory store."""

import json
import logging
import time
from collections import OrderedDict, defaultdict

from core.config import settings

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as aioredis
    from redis.exceptions import WatchError
    _HAS_REDIS = True
except ImportError:
    logger.warning("redis-py not installed, using in-memory fallback")
    _HAS_REDIS = False
    class WatchError(Exception):  # type: ignore
        pass



# ── Pool ────────────────────────────────────────────────────────────────

_pool: "aioredis.Redis | None" = None


async def init_redis() -> None:
    global _pool
    if not _HAS_REDIS:
        logger.info("Redis: using in-memory fallback (redis-py not installed)")
        return
    try:
        url = settings.redis_url
        _pool = aioredis.from_url(url, decode_responses=True, socket_timeout=2)
        await _pool.ping()
        logger.info("Redis connected: %s", url)
    except Exception as e:
        logger.warning("Redis unavailable (%s), using in-memory fallback", e)
        _pool = None


async def close_redis() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None
        logger.info("Redis connection closed")


def _redis() -> "aioredis.Redis | None":
    return _pool


# ── Review Store ────────────────────────────────────────────────────────

REVIEW_TTL = 3600
REVIEW_KEY_PREFIX = "review:"

_INMEM_REVIEWS_MAX = 1000
_inmem_reviews: OrderedDict[str, dict] = OrderedDict()


async def review_store_set(review_id: str, data: dict) -> None:
    r = _redis()
    if r is not None:
        await r.setex(f"{REVIEW_KEY_PREFIX}{review_id}", REVIEW_TTL, json.dumps(data, default=str))
    else:
        if len(_inmem_reviews) >= _INMEM_REVIEWS_MAX:
            _inmem_reviews.popitem(last=False)
        _inmem_reviews[review_id] = json.loads(json.dumps(data, default=str))


async def review_store_get(review_id: str) -> dict | None:
    r = _redis()
    if r is not None:
        raw = await r.get(f"{REVIEW_KEY_PREFIX}{review_id}")
        if raw is None:
            return None
        return json.loads(raw)
    return _inmem_reviews.get(review_id)


async def review_store_update(review_id: str, data: dict) -> None:
    r = _redis()
    if r is not None:
        async with r.pipeline(transaction=True) as pipeline:
            while True:
                try:
                    await pipeline.watch(f"{REVIEW_KEY_PREFIX}{review_id}")
                    existing = await pipeline.get(f"{REVIEW_KEY_PREFIX}{review_id}")
                    if existing is not None:
                        parsed = json.loads(existing)
                        parsed.update(data)
                    else:
                        parsed = data
                    pipeline.multi()
                    pipeline.setex(
                        f"{REVIEW_KEY_PREFIX}{review_id}", REVIEW_TTL,
                        json.dumps(parsed, default=str),
                    )
                    await pipeline.execute()
                    break
                except WatchError:
                    continue
        return
    existing_mem = _inmem_reviews.get(review_id)
    if existing_mem is not None:
        existing_mem.update(json.loads(json.dumps(data, default=str)))
    else:
        if len(_inmem_reviews) >= _INMEM_REVIEWS_MAX:
            _inmem_reviews.popitem(last=False)
        _inmem_reviews[review_id] = json.loads(json.dumps(data, default=str))


async def review_store_cleanup() -> None:
    """No-op for Redis (TTL handles it). Clean in-memory stale entries."""
    from datetime import datetime
    now = time.time()
    stale = []
    for rid, d in list(_inmem_reviews.items()):
        comp = d.get("completed_at")
        if comp:
            try:
                if isinstance(comp, str):
                    # Replace Z with +00:00 to support older python fromisoformat
                    comp_t = datetime.fromisoformat(comp.replace("Z", "+00:00")).timestamp()
                else:
                    comp_t = float(comp)
                if now - comp_t > REVIEW_TTL:
                    stale.append(rid)
            except Exception:
                stale.append(rid)
    for rid in stale:
        _inmem_reviews.pop(rid, None)


# ── Rate Limiter ────────────────────────────────────────────────────────

RATE_LIMIT_KEY_PREFIX = "ratelimit:"
_INMEM_RATE_LIMITS_MAX = 10000
_inmem_rate_limits: dict[str, list[float]] = defaultdict(list)


async def rate_limit_check(ip: str, limit: int = 10, window: int = 3600, key_prefix: str = RATE_LIMIT_KEY_PREFIX) -> bool:
    """Returns True if allowed, False if rate limited."""
    now = time.time()
    cutoff = now - window
    mem_key = f"{key_prefix}{ip}"

    r = _redis()
    if r is not None:
        key = f"{key_prefix}{ip}"
        pipe = r.pipeline()
        pipe.zremrangebyscore(key, 0, cutoff)
        pipe.zcard(key)
        results = await pipe.execute()
        count = results[1]
        if count >= limit:
            return False
        await r.zadd(key, {str(int(now)): now})
        await r.expire(key, window)
        return True
    else:
        _inmem_rate_limits[mem_key] = [t for t in _inmem_rate_limits[mem_key] if t > cutoff]
        if len(_inmem_rate_limits[mem_key]) >= limit:
            return False
        _inmem_rate_limits[mem_key].append(now)
        if len(_inmem_rate_limits) > _INMEM_RATE_LIMITS_MAX:
            _inmem_rate_limits.pop(next(iter(_inmem_rate_limits)), None)
        return True


async def rate_limit_reset() -> None:
    r = _redis()
    if r is not None:
        cursor = 0
        while True:
            cursor, keys = await r.scan(cursor=cursor, match=f"{RATE_LIMIT_KEY_PREFIX}*", count=100)
            if keys:
                await r.delete(*keys)
            if cursor == 0:
                break
    _inmem_rate_limits.clear()


# ── Brute Force Protection ────────────────────────────────────────────

BF_KEY_PREFIX = "bf:"
_INMEM_BF: dict[str, list[float]] = defaultdict(list)
_INMEM_BF_MAX = 10000

async def failed_login_attempt(identifier: str, lockout_seconds: int = 900) -> int:
    """Record a failed login. Returns the current attempt count."""
    now = time.time()
    cutoff = now - lockout_seconds
    r = _redis()
    if r is not None:
        key = f"{BF_KEY_PREFIX}{identifier}"
        pipe = r.pipeline()
        pipe.zremrangebyscore(key, 0, cutoff)
        pipe.zcard(key)
        results = await pipe.execute()
        count = results[1] + 1
        await r.zadd(key, {str(int(now * 1000)): now})
        await r.expire(key, lockout_seconds)
        return count
    _INMEM_BF[identifier] = [t for t in _INMEM_BF[identifier] if t > cutoff]
    _INMEM_BF[identifier].append(now)
    if len(_INMEM_BF) > _INMEM_BF_MAX:
        _INMEM_BF.pop(next(iter(_INMEM_BF)), None)
    return len(_INMEM_BF[identifier])


async def is_login_locked(identifier: str, max_attempts: int = 5, lockout_seconds: int = 900) -> bool:
    """Returns True if the identifier is currently locked out."""
    now = time.time()
    cutoff = now - lockout_seconds
    r = _redis()
    if r is not None:
        key = f"{BF_KEY_PREFIX}{identifier}"
        count = await r.zcount(key, cutoff, now)
        return int(count) >= max_attempts
    entries = [t for t in _INMEM_BF[identifier] if t > cutoff]
    return len(entries) >= max_attempts


async def reset_login_attempts(identifier: str) -> None:
    """Clear failed attempts on successful login."""
    r = _redis()
    if r is not None:
        await r.delete(f"{BF_KEY_PREFIX}{identifier}")
    _INMEM_BF.pop(identifier, None)


async def brute_force_reset() -> None:
    """Clear all brute force tracking (for tests)."""
    r = _redis()
    if r is not None:
        cursor = 0
        while True:
            cursor, keys = await r.scan(cursor=cursor, match=f"{BF_KEY_PREFIX}*", count=100)
            if keys:
                await r.delete(*keys)
            if cursor == 0:
                break
    _INMEM_BF.clear()


# Compatibility aliases
get_review_state = review_store_get
check_rate_limit = rate_limit_check

