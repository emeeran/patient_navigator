"""Redis-backed rate limiter for login attempts."""

from app.core.config import settings
from app.core.exceptions import RateLimitExceededError

# In-memory fallback when Redis is unavailable
_memory_store: dict[str, list[float]] = {}


def _make_key(email: str, ip: str) -> str:
    return f"ratelimit:login:{email.lower()}:{ip}"


def _get_times(key: str) -> list[float]:
    """Get stored attempt timestamps (in-memory fallback)."""
    import time
    entries = _memory_store.get(key, [])
    now = time.time()
    # Prune expired entries
    window = settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    entries = [t for t in entries if now - t < window]
    _memory_store[key] = entries
    return entries


async def check_rate_limit(email: str, ip: str) -> None:
    """Raise RateLimitExceededError if too many failed attempts."""
    key = _make_key(email, ip)
    entries = _get_times(key)
    if len(entries) >= settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS:
        raise RateLimitExceededError()


async def record_failed_attempt(email: str, ip: str) -> None:
    """Record a failed login attempt."""
    import time
    key = _make_key(email, ip)
    if key not in _memory_store:
        _memory_store[key] = []
    _memory_store[key].append(time.time())


async def clear_rate_limit(email: str, ip: str) -> None:
    """Clear rate limit on successful login."""
    key = _make_key(email, ip)
    _memory_store.pop(key, None)
