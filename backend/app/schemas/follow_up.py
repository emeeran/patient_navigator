"""Pydantic schemas for Follow-Up Tracking — FEAT-008."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

FOLLOW_UP_TYPES = ("appointment", "checkup", "lab_test", "imaging", "referral")
FOLLOW_UP_STATUSES = ("scheduled", "completed", "overdue", "cancelled")


class FollowUpCreateRequest(BaseModel):
    """Create a new follow-up."""

    scheduled_date: datetime
    follow_up_type: str
    notes: str | None = None


class FollowUpUpdateRequest(BaseModel):
    """Update a follow-up."""

    scheduled_date: datetime | None = None
    follow_up_type: str | None = None
    notes: str | None = None
    status: str | None = None


class FollowUpResponse(BaseModel):
    """Full follow-up response."""

    id: UUID
    case_id: UUID
    scheduled_date: datetime
    follow_up_type: str
    status: str
    notes: str | None
    completed_at: datetime | None
    completed_by: UUID | None
    reminder_sent: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class FollowUpListItem(BaseModel):
    """Follow-up list item."""

    id: UUID
    case_id: UUID
    scheduled_date: datetime
    follow_up_type: str
    status: str
    created_by: UUID
    created_at: datetime


class FollowUpListResponse(BaseModel):
    """Paginated follow-up list."""

    items: list[FollowUpListItem]
    total: int
    page: int
    per_page: int


# ── ORM → dict helpers ──────────────────────────────────


def follow_up_to_dict(fu: object) -> dict:
    """Convert a FollowUp ORM object to a full response dict."""
    return {
        "id": fu.id,
        "case_id": fu.case_id,
        "scheduled_date": fu.scheduled_date,
        "follow_up_type": fu.follow_up_type,
        "status": fu.status,
        "notes": fu.notes,
        "completed_at": fu.completed_at,
        "completed_by": fu.completed_by,
        "reminder_sent": fu.reminder_sent,
        "created_by": fu.created_by,
        "created_at": fu.created_at,
        "updated_at": fu.updated_at,
    }


def follow_up_list_item_to_dict(fu: object) -> dict:
    """Convert a FollowUp ORM to a list item dict."""
    return {
        "id": fu.id,
        "case_id": fu.case_id,
        "scheduled_date": fu.scheduled_date,
        "follow_up_type": fu.follow_up_type,
        "status": fu.status,
        "created_by": fu.created_by,
        "created_at": fu.created_at,
    }
