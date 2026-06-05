"""Settings service — registry, CRUD, live reload, and health checks."""

import asyncio
import logging
import uuid
from dataclasses import dataclass

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.system_setting import SystemSetting
from app.services.auth_service import write_audit_log

logger = logging.getLogger(__name__)

MASK = "••••••••••"


@dataclass
class SettingMeta:
    """Metadata for a single configurable setting."""

    type: str  # "str", "int", "bool"
    group: str  # "app", "auth", "ai", "files", "cors", "infra"
    editable: bool
    sensitive: bool


SETTINGS_REGISTRY: dict[str, SettingMeta] = {
    # ── Application ───────────────────────────
    "APP_NAME": SettingMeta(type="str", group="app", editable=False, sensitive=False),
    "APP_VERSION": SettingMeta(type="str", group="app", editable=False, sensitive=False),
    "DEBUG": SettingMeta(type="bool", group="app", editable=False, sensitive=False),
    "ENVIRONMENT": SettingMeta(type="str", group="app", editable=False, sensitive=False),
    # ── Authentication & Security ─────────────
    "ACCESS_TOKEN_EXPIRE_MINUTES": SettingMeta(type="int", group="auth", editable=True, sensitive=False),
    "REFRESH_TOKEN_EXPIRE_DAYS": SettingMeta(type="int", group="auth", editable=True, sensitive=False),
    "BCRYPT_ROUNDS": SettingMeta(type="int", group="auth", editable=True, sensitive=False),
    "LOGIN_RATE_LIMIT_MAX_ATTEMPTS": SettingMeta(type="int", group="auth", editable=True, sensitive=False),
    "LOGIN_RATE_LIMIT_WINDOW_SECONDS": SettingMeta(type="int", group="auth", editable=True, sensitive=False),
    "JWT_ALGORITHM": SettingMeta(type="str", group="auth", editable=False, sensitive=False),
    "JWT_SECRET_KEY": SettingMeta(type="str", group="auth", editable=False, sensitive=True),
    # ── AI / LLM ──────────────────────────────
    "OLLAMA_BASE_URL": SettingMeta(type="str", group="ai", editable=True, sensitive=False),
    "DEFAULT_MODEL": SettingMeta(type="str", group="ai", editable=True, sensitive=False),
    "OLLAMA_TIMEOUT": SettingMeta(type="int", group="ai", editable=True, sensitive=False),
    # ── File Storage ──────────────────────────
    "UPLOAD_DIR": SettingMeta(type="str", group="files", editable=False, sensitive=False),
    "MAX_UPLOAD_SIZE_BYTES": SettingMeta(type="int", group="files", editable=True, sensitive=False),
    # ── CORS ──────────────────────────────────
    "CORS_ORIGINS": SettingMeta(type="str", group="cors", editable=True, sensitive=False),
    # ── Infrastructure ────────────────────────
    "DATABASE_URL": SettingMeta(type="str", group="infra", editable=False, sensitive=True),
    "DATABASE_URL_SYNC": SettingMeta(type="str", group="infra", editable=False, sensitive=True),
    "REDIS_URL": SettingMeta(type="str", group="infra", editable=False, sensitive=True),
}

GROUP_LABELS: dict[str, str] = {
    "app": "Application",
    "auth": "Authentication & Security",
    "ai": "AI / LLM",
    "files": "File Storage",
    "cors": "CORS",
    "infra": "Database & Redis",
}


def _coerce(value: str, type_name: str):
    """Convert a string value to the expected Python type."""
    if type_name == "int":
        return int(value)
    if type_name == "bool":
        return value.lower() in ("true", "1", "yes")
    return value


class SettingsService:
    """Read, update, and health-check system settings."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_settings(self) -> list[dict]:
        """Return all settings with effective values (DB override → .env default)."""
        # Load all overrides from DB
        result = await self.db.execute(select(SystemSetting))
        overrides = {s.key: s for s in result.scalars().all()}

        items = []
        for key, meta in SETTINGS_REGISTRY.items():
            default_value = str(getattr(settings, key, ""))
            override = overrides.get(key)

            if override:
                raw_value = override.value
                source = "database"
            else:
                raw_value = default_value
                source = "default"

            display_value = MASK if meta.sensitive else raw_value

            items.append({
                "key": key,
                "value": "" if meta.sensitive else raw_value,
                "display_value": display_value,
                "type": meta.type,
                "group_name": meta.group,
                "editable": meta.editable,
                "sensitive": meta.sensitive,
                "source": source,
            })

        return items

    async def update_settings(
        self,
        updates: dict[str, str],
        user_id: uuid.UUID,
    ) -> list[str]:
        """Validate, persist, and apply setting overrides. Returns list of updated keys."""
        updated_keys: list[str] = []

        for key, new_value in updates.items():
            meta = SETTINGS_REGISTRY.get(key)
            if not meta:
                raise ValueError(f"Unknown setting: {key}")
            if not meta.editable:
                raise ValueError(f"Setting '{key}' is not editable")
            # Validate type coercion
            try:
                _coerce(new_value, meta.type)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid value for '{key}': {e}") from e

            # Upsert into DB
            result = await self.db.execute(
                select(SystemSetting).where(SystemSetting.key == key)
            )
            existing = result.scalar_one_or_none()
            if existing:
                existing.value = new_value
                existing.updated_by = user_id
            else:
                self.db.add(SystemSetting(
                    key=key,
                    value=new_value,
                    value_type=meta.type,
                    group_name=meta.group,
                    editable=meta.editable,
                    updated_by=user_id,
                ))

            # Apply to runtime settings singleton
            typed_value = _coerce(new_value, meta.type)
            object.__setattr__(settings, key, typed_value)

            # Audit log
            await write_audit_log(
                self.db,
                action="settings.updated",
                user_id=user_id,
                entity_type="setting",
                description=f"Updated {key} = {new_value}",
            )

            updated_keys.append(key)

        await self.db.flush()
        return updated_keys

    async def check_service_health(self) -> dict:
        """Check connectivity to PostgreSQL, Redis, and Ollama."""
        # PostgreSQL
        try:
            result = await self.db.execute(select(1))
            _ = result.scalar()
            pg_status = "ok"
        except Exception:
            pg_status = "unreachable"

        # Redis (TCP check)
        redis_status = await _check_redis(settings.REDIS_URL)

        # Ollama
        ollama_status, ollama_models = await _check_ollama(
            settings.OLLAMA_BASE_URL
        )

        return {
            "postgres": pg_status,
            "redis": redis_status,
            "ollama": ollama_status,
            "ollama_models": ollama_models,
        }


async def _check_redis(redis_url: str) -> str:
    """Check Redis connectivity via TCP connection."""
    try:
        from urllib.parse import urlparse

        parsed = urlparse(redis_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 6379
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=3.0
        )
        writer.close()
        await writer.wait_closed()
        return "ok"
    except Exception:
        return "unreachable"


async def _check_ollama(base_url: str) -> tuple[str, list[str] | None]:
    """Check Ollama connectivity and list available models."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{base_url}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                return "ok", models
            return "unreachable", None
    except Exception:
        return "unreachable", None
