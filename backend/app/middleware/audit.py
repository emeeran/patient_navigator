"""Audit middleware helpers."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def write_audit_log(
    db: AsyncSession,
    action: str,
    user_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    description: str | None = None,
    metadata: dict | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Write an entry to the audit log. Re-exported for convenience."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        metadata_=metadata,
        ip_address=ip_address,
    )
    db.add(entry)
    await db.flush()
    return entry
