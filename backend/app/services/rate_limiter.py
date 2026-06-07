"""Redis-backed rate limiter for login attempts.

Uses Redis Sorted Sets for a sliding-window rate limiting strategy.
Falls back to in-memory storage when Redis is unavailable so the app
remains functional even if Redis goes down.
"""

import logging
import time
from contextlib import suppress

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.exceptions import RateLimitExceededError

logger = logging.getLogger(__name__)

# ── Redis connection pool (lazy-initialised) ──────────
_redis_pool: aioredis.Redis | None = None


async def _get_redis() -> aioredis.Redis | None:
    """Return the shared Redis client, or None if Redis is unreachable."""
    global _redis_pool
    if _redis_pool is not None:
        return _redis_pool
    try:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        await _redis_pool.ping()
        logger.info("Rate limiter connected to Redis")
        return _redis_pool
    except Exception as exc:
        logger.warning("Redis unavailable for rate limiting (%s) — using in-memory fallback", exc)
        _redis_pool = None
        return None


async def close_redis() -> None:
    """Close the Redis connection pool (called on app shutdown)."""
    global _redis_pool
    if _redis_pool is not None:
        with suppress(Exception):
            await _redis_pool.aclose()
        _redis_pool = None


# ── In-memory fallback ───────────────────────────────
_memory_store: dict[str, list[float]] = {}


def _make_key(email: str, ip: str) -> str:
    return f"ratelimit:login:{email.lower()}:{ip}"


# ── Public API ────────────────────────────────────────

async def check_rate_limit(email: str, ip: str) -> None:
    """Raise RateLimitExceededError if too many failed attempts."""
    key = _make_key(email, ip)
    window = settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    max_attempts = settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS
    now = time.time()
    window_start = now - window

    rdb = await _get_redis()
    if rdb is not None:
        # Redis sliding-window: remove old entries, count remaining
        pipe = rdb.pipeline(transaction=True)
        pipe.zremrangebyscore(key, "-inf", window_start)
        pipe.zcard(key)
        _, count = await pipe.execute()
        if count >= max_attempts:
            raise RateLimitExceededError()
        return

    # In-memory fallback
    entries = _memory_store.get(key, [])
    entries = [t for t in entries if now - t < window]
    _memory_store[key] = entries
    if len(entries) >= max_attempts:
        raise RateLimitExceededError()


async def record_failed_attempt(email: str, ip: str) -> None:
    """Record a failed login attempt."""
    key = _make_key(email, ip)
    now = time.time()

    rdb = await _get_redis()
    if rdb is not None:
        pipe = rdb.pipeline(transaction=True)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS)
        await pipe.execute()
        return

    # In-memory fallback
    if key not in _memory_store:
        _memory_store[key] = []
    _memory_store[key].append(now)


async def clear_rate_limit(email: str, ip: str) -> None:
    """Clear rate limit on successful login."""
    key = _make_key(email, ip)

    rdb = await _get_redis()
    if rdb is not None:
        with suppress(Exception):
            await rdb.delete(key)
        return

    # In-memory fallback
    _memory_store.pop(key, None)
