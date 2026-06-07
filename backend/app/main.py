"""FastAPI application entry point."""

import asyncio
import logging
import shutil
import subprocess
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


async def _ollama_is_responding(timeout: float = 3.0) -> tuple[bool, list[str]]:
    """Check if Ollama API is reachable. Returns (ok, model_names)."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if resp.status_code != 200:
                return False, []
            models = [m.get("name", "") for m in resp.json().get("models", [])]
            return True, models
    except Exception:
        return False, []


async def _start_ollama_service() -> bool:
    """Attempt to start the Ollama service (systemd or direct).

    Returns True if we managed to launch it (or it was already running).
    """
    # Skip auto-start in containers / CI where ollama CLI won't exist
    if not shutil.which("ollama"):
        logger.warning("ollama CLI not found — cannot auto-start. Install: https://ollama.com")
        return False

    # Try systemd first
    if shutil.which("systemctl"):
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "ollama"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.stdout.strip() == "active":
                logger.info("Ollama systemd service is active")
                return True
            # Try starting it
            subprocess.run(
                ["systemctl", "start", "ollama"],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
            pass

    # If systemd didn't work or isn't available, launch directly
    responding, _ = await _ollama_is_responding()
    if responding:
        return True

    logger.info("Starting Ollama via `ollama serve` ...")
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as exc:
        logger.warning("Failed to start ollama serve: %s", exc)
        return False

    # Wait up to 30s for Ollama to start responding
    for attempt in range(30):
        responding, _ = await _ollama_is_responding()
        if responding:
            logger.info("Ollama started after %.0fs", attempt + 1)
            return True
        await asyncio.sleep(1)

    logger.warning("Ollama did not respond within 30s")
    return False


async def _pull_model_if_missing(models: list[str]) -> bool:
    """Pull the configured model if it's not already available."""
    if settings.DEFAULT_MODEL in models:
        logger.info("Model %s already available — skipping pull", settings.DEFAULT_MODEL)
        return True

    if not shutil.which("ollama"):
        return False

    logger.info("Pulling model %s (first run may take a while) ...", settings.DEFAULT_MODEL)
    try:
        proc = await asyncio.create_subprocess_exec(
            "ollama", "pull", settings.DEFAULT_MODEL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=600)
        if proc.returncode == 0:
            logger.info("Model %s pulled successfully", settings.DEFAULT_MODEL)
            return True
        else:
            logger.warning("ollama pull failed (exit %d): %s", proc.returncode, stdout.decode()[:200])
            return False
    except TimeoutError:
        logger.warning("ollama pull timed out after 600s")
        return False
    except Exception as exc:
        logger.warning("Failed to pull model: %s", exc)
        return False


async def _ensure_ollama() -> bool:
    """Ensure Ollama is running and the required model is available.

    1. Check if Ollama is already responding.
    2. If not, try to start it (systemd → direct launch).
    3. Pull the configured model if missing.
    """
    # Step 1: Is it already running?
    responding, models = await _ollama_is_responding()
    if responding:
        logger.info("Ollama is running (%d models available)", len(models))
        # Still might need to pull the model
        if await _pull_model_if_missing(models):
            logger.info("Ollama ready — model %s available", settings.DEFAULT_MODEL)
            return True
        logger.warning("Ollama running but model %s could not be pulled", settings.DEFAULT_MODEL)
        return False

    # Step 2: Try to start it (skip in production/containers)
    if settings.is_production:
        logger.warning(
            "Ollama not reachable at %s — AI features disabled. "
            "In production, ensure Ollama is running separately.",
            settings.OLLAMA_BASE_URL,
        )
        return False

    started = await _start_ollama_service()
    if not started:
        logger.warning(
            "Could not start Ollama — AI features disabled. "
            "Start manually: ollama serve",
        )
        return False

    # Step 3: Pull the model if needed
    responding, models = await _ollama_is_responding()
    if not responding:
        logger.warning("Ollama started but not responding — AI features disabled")
        return False

    if await _pull_model_if_missing(models):
        logger.info("Ollama ready — model %s available", settings.DEFAULT_MODEL)
        return True

    logger.warning("Ollama running but model %s could not be pulled", settings.DEFAULT_MODEL)
    return False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: configure logging, verify services, clean up on shutdown."""
    setup_logging(environment=settings.ENVIRONMENT)
    global _start_time
    _start_time = datetime.now(UTC)
    logger.info("Starting %s v%s (%s)", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)

    ollama_ok = await _ensure_ollama()
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
        from sqlalchemy import text

        from app.core.database import engine

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
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
