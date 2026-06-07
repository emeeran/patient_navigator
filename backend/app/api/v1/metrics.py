"""Lightweight application metrics endpoint.

Returns operational counters and health data for monitoring.
For production observability, consider prometheus-fastapi-instrumentator.
"""

import os
import time

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()

# Track request counts in-memory (per-process; aggregate across workers externally)
_request_counts: dict[str, int] = {
    "total": 0,
    "2xx": 0,
    "4xx": 0,
    "5xx": 0,
}
_start_time = time.time()


def record_request(status_code: int) -> None:
    """Call from middleware to track request counts."""
    _request_counts["total"] += 1
    category = f"{status_code // 100}xx"
    if category in _request_counts:
        _request_counts[category] += 1


@router.get("/metrics", tags=["System"], include_in_schema=False)
async def metrics() -> dict:
    """Lightweight operational metrics."""
    import psutil

    process = psutil.Process(os.getpid())
    uptime = time.time() - _start_time

    # Database pool stats
    db_pool_info: dict = {}
    try:
        from app.core.database import engine

        pool = engine.pool
        db_pool_info = {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
        }
    except Exception:
        db_pool_info = {"status": "unavailable"}

    # Redis status
    redis_ok = False
    try:
        from app.services.rate_limiter import _get_redis

        rdb = await _get_redis()
        redis_ok = rdb is not None and await rdb.ping()
    except (ConnectionError, TimeoutError, OSError):
        pass

    mem_info = process.memory_info()

    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": round(uptime, 1),
        "requests": _request_counts,
        "database_pool": db_pool_info,
        "redis": "ok" if redis_ok else "unavailable",
        "memory_mb": round(mem_info.rss / 1024 / 1024, 1),
    }
