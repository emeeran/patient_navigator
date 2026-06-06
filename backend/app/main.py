"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: verify database connectivity on startup."""
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ── Exception Handlers ───────────────────────────────
register_exception_handlers(app)

# ── CORS ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Health Check (API-098) ────────────────────────────
@app.get("/health", tags=["System"])
async def health_check() -> dict:
    return {"status": "healthy", "version": settings.APP_VERSION}

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
