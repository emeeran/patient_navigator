"""Pydantic schemas for audit log endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    action: str
    entity_type: str | None
    entity_id: UUID | None
    description: str | None
    metadata_: dict | None = None
    ip_address: str | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogEntry]
    total: int
    page: int
    limit: int
