"""Async SQLAlchemy engine, session factory, and Base declarative model."""

import contextlib
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "command_timeout": 10,
        "server_settings": {"application_name": "patient_nav"},
    },
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session and closes it."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            with contextlib.suppress(Exception):
                await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables (used in testing; production uses Alembic)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
