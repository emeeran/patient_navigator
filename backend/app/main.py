"""FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

logger = logging.getLogger(__name__)

# Track application start time for uptime metric
_start_time: datetime | None = None


async def _check_ollama() -> bool:
    """Check if Ollama is reachable and the default model is available."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if resp.status_code != 200:
                return False
            models = [m.get("name", "") for m in resp.json().get("models", [])]
            if settings.DEFAULT_MODEL in models:
                logger.info(
                    "Ollama ready — model %s available (%d models total)",
                    settings.DEFAULT_MODEL,
                    len(models),
                )
                return True
            else:
                logger.warning(
                    "Ollama running but model %s not found. "
                    "Available: %s. Run: ollama pull %s",
                    settings.DEFAULT_MODEL,
                    ", ".join(models) or "(none)",
                    settings.DEFAULT_MODEL,
                )
                return False
    except httpx.ConnectError:
        logger.warning(
            "Ollama not reachable at %s — AI features disabled. "
            "Start it with: ollama serve  or  sudo systemctl start ollama",
            settings.OLLAMA_BASE_URL,
        )
        return False
    except Exception as exc:
        logger.warning("Ollama health check failed: %s", exc)
        return False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: configure logging, verify services, clean up on shutdown."""
    setup_logging(environment=settings.ENVIRONMENT)
    global _start_time
    _start_time = datetime.now(UTC)
    logger.info("Starting %s v%s (%s)", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)

    ollama_ok = await _check_ollama()
    app.state.ollama_ready = ollama_ok
    yield

    # ── Graceful shutdown ──────────────────────────────
    logger.info("Shutting down %s...", settings.APP_NAME)
    from app.services.rate_limiter import close_redis
    await close_redis()
    from app.core.database import engine
    await engine.dispose()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ── Exception Handlers ───────────────────────────────
register_exception_handlers(app)

# ── Security Headers ────────────────────────────────
app.add_middleware(SecurityHeadersMiddleware)

# ── Request ID ────────────────────────────────────────
app.add_middleware(RequestIdMiddleware)

# ── CORS ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ── Health Check (API-098) ────────────────────────────
async def _check_db() -> bool:
    """Test database connectivity."""
    try:
        from app.core.database import engine

        async with engine.connect() as conn:
            await conn.execute(type(conn).sync_connection.text("SELECT 1"))
        return True
    except Exception:
        return False


async def _check_redis() -> bool:
    """Test Redis connectivity."""
    try:
        from app.services.rate_limiter import _get_redis

        rdb = await _get_redis()
        return rdb is not None and await rdb.ping()
    except Exception:
        return False


@app.get("/health", tags=["System"])
async def health_check() -> JSONResponse:
    """Enhanced health check with dependency status."""
    checks = {
        "database": "ok" if await _check_db() else "fail",
        "redis": "ok" if await _check_redis() else "fail",
        "ollama": "ok" if getattr(app.state, "ollama_ready", False) else "fail",
    }

    all_ok = all(v == "ok" for v in checks.values())
    critical_ok = checks["database"] == "ok"

    if critical_ok and all_ok:
        status, http_code = "healthy", 200
    elif critical_ok:
        status, http_code = "degraded", 200
    else:
        status, http_code = "unhealthy", 503

    uptime_seconds = (
        (datetime.now(UTC) - _start_time).total_seconds() if _start_time else 0
    )

    return JSONResponse(
        status_code=http_code,
        content={
            "status": status,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "uptime_seconds": round(uptime_seconds, 1),
            "checks": checks,
        },
    )

# ── Router includes ──────────────────────────────────
from app.api.v1.admin import router as admin_router  # noqa: E402
from app.api.v1.ai import router as ai_router  # noqa: E402
from app.api.v1.auth import router as auth_router  # noqa: E402
from app.api.v1.cases import router as cases_router  # noqa: E402
from app.api.v1.documents import router as documents_router  # noqa: E402
from app.api.v1.follow_ups import router as follow_ups_router  # noqa: E402
from app.api.v1.funding import router as funding_router  # noqa: E402
from app.api.v1.hospitals import router as hospitals_router  # noqa: E402
from app.api.v1.medical_profiles import router as medical_profiles_router  # noqa: E402
from app.api.v1.metrics import router as metrics_router  # noqa: E402
from app.api.v1.patients import router as patients_router  # noqa: E402

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(admin_router, prefix="/admin", tags=["Administration"])
app.include_router(patients_router, prefix="/patients", tags=["Patients"])
app.include_router(medical_profiles_router, prefix="/patients", tags=["Medical Profiles"])
app.include_router(cases_router, prefix="", tags=["Cases"])
app.include_router(documents_router, prefix="", tags=["Documents"])
app.include_router(ai_router, prefix="", tags=["AI & Reviews"])
app.include_router(follow_ups_router, prefix="", tags=["Follow-Ups"])
app.include_router(funding_router, prefix="", tags=["Funding"])
app.include_router(hospitals_router, prefix="", tags=["Hospitals"])
app.include_router(metrics_router)
