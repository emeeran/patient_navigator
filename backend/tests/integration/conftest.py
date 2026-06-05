"""
Integration Test Fixtures — Patient Navigator Platform
Shared fixtures for all integration test modules.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import Base, get_db

# ── Test database URL ─────────────────────────────────
TEST_DATABASE_URL = settings.DATABASE_URL.replace("/patient_nav", "/patient_nav_test")

_tables_created = False


async def _ensure_seeded(engine):
    """Create tables (once per process) and ensure seed data is correct (every time).

    Seed data is refreshed each call because integration tests (e.g. auth RBAC)
    may mutate seeded users via admin endpoints. The seed function is idempotent:
    it creates missing records and updates existing ones to match expected state.
    """
    global _tables_created
    if not _tables_created:
        async with engine.begin() as conn:
            # Enable pg_trgm extension for GIN trigram fuzzy search indexes
            await conn.execute(
                __import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS pg_trgm")
            )
            await conn.run_sync(Base.metadata.create_all)
        _tables_created = True

    # Always re-seed to fix any mutations from previous tests
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        from tests.seed import cleanup_test_artifacts, seed_test_data

        await cleanup_test_artifacts(session)
        await seed_test_data(session)
        await session.commit()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an httpx.AsyncClient wired to the FastAPI app via ASGI transport.
    Creates a fresh engine per test to avoid asyncpg event loop issues.
    """
    from app.main import app

    # Create a fresh engine with NullPool so each connection is new
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    await _ensure_seeded(engine)

    async def _get_db():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async session for direct DB assertions."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


# ── Helper: obtain a JWT token for a given role ───────

async def _get_token_for_role(client: AsyncClient, role: str) -> str:
    """Log in as the seeded test user for *role* and return the access token."""
    resp = await client.post(
        "/auth/login",
        json={"email": f"{role}@test.com", "password": "TestPass123!"},
    )
    assert resp.status_code == 200, f"Login failed for {role}: {resp.text}"
    return resp.json()["access_token"]


def _bearer_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ── Per-role auth header fixtures ─────────────────────

@pytest_asyncio.fixture
async def auth_headers_admin(async_client: AsyncClient) -> dict[str, str]:
    token = await _get_token_for_role(async_client, "admin")
    return _bearer_headers(token)


@pytest_asyncio.fixture
async def auth_headers_navigator(async_client: AsyncClient) -> dict[str, str]:
    token = await _get_token_for_role(async_client, "navigator")
    return _bearer_headers(token)


@pytest_asyncio.fixture
async def auth_headers_clinician(async_client: AsyncClient) -> dict[str, str]:
    token = await _get_token_for_role(async_client, "clinician")
    return _bearer_headers(token)


@pytest_asyncio.fixture
async def auth_headers_volunteer(async_client: AsyncClient) -> dict[str, str]:
    token = await _get_token_for_role(async_client, "volunteer")
    return _bearer_headers(token)


@pytest_asyncio.fixture
async def auth_headers_patient(async_client: AsyncClient) -> dict[str, str]:
    token = await _get_token_for_role(async_client, "patient")
    return _bearer_headers(token)


# ── Custom pytest markers ─────────────────────────────

def pytest_configure(config):
    """Register custom markers used by integration tests."""
    config.addinivalue_line("markers", "spec(spec_id): link test to a spec ID")
    config.addinivalue_line("markers", "performance: performance benchmark test")
    config.addinivalue_line("markers", "observability: observability / audit test")


# ── Seeded entity ID fixtures ─────────────────────────
import uuid as _uuid

from tests.seed import SEED_CASE_IDS, SEED_PATIENT_IDS  # noqa: E402


@pytest.fixture
def seeded_patient_id() -> _uuid.UUID:
    """ID of the primary test patient (Aarav Mehta, active)."""
    return SEED_PATIENT_IDS["p001"]


@pytest.fixture
def seeded_patient_id_2() -> _uuid.UUID:
    """ID of a second test patient (Arun Kumar, active)."""
    return SEED_PATIENT_IDS["p002"]


@pytest.fixture
def seeded_patient_id_3() -> _uuid.UUID:
    """ID of a third test patient (Priya Sharma, active)."""
    return SEED_PATIENT_IDS["p003"]


@pytest.fixture
def seeded_archived_patient_id() -> _uuid.UUID:
    """ID of the archived test patient."""
    return SEED_PATIENT_IDS["p_archived"]


@pytest.fixture
def seeded_own_patient_id() -> _uuid.UUID:
    """ID of patient record owned by patient-role user for ownership tests."""
    return SEED_PATIENT_IDS["p_own"]


@pytest.fixture
def seeded_case_id_new() -> _uuid.UUID:
    """ID of a case with status 'new'."""
    return SEED_CASE_IDS["c001"]


@pytest.fixture
def seeded_case_id_under_review() -> _uuid.UUID:
    """ID of a case with status 'under_review'."""
    return SEED_CASE_IDS["c002"]


@pytest.fixture
def seeded_case_id_closed() -> _uuid.UUID:
    """ID of a case with status 'closed'."""
    return SEED_CASE_IDS["c003"]
