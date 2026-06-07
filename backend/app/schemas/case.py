"""Pydantic schemas for Case endpoints — DATA-004, API-020..026."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.validators import check_at_least_one

# ── Enums ──────────────────────────────────────────────
CASE_STATUS_VALUES = (
    "new",
    "under_review",
    "hospital_selected",
    "funding_applied",
    "treatment_started",
    "closed",
)
CASE_PRIORITY_VALUES = ("low", "medium", "high", "critical")

# ── Request schemas ─────────────────────────────────────


class CaseCreateRequest(BaseModel):
    """POST /patients/{patientId}/cases."""

    diagnosis: str = Field(..., min_length=1, max_length=5000)
    priority: Literal[CASE_PRIORITY_VALUES] = "medium"
    notes: str | None = Field(None, max_length=10000)
    recommended_hospital_id: UUID | None = None
    applied_funding_id: UUID | None = None
    assigned_clinician_id: UUID | None = None


class CaseUpdateRequest(BaseModel):
    """PATCH /cases/{id} — at least one field required."""

    diagnosis: str | None = Field(None, min_length=1, max_length=5000)
    priority: Literal[CASE_PRIORITY_VALUES] | None = None
    notes: str | None = Field(None, max_length=10000)
    recommended_hospital_id: UUID | None = None
    applied_funding_id: UUID | None = None
    assigned_clinician_id: UUID | None = None

    @model_validator(mode="after")
    def at_least_one_field(self):
        check_at_least_one(
            self,
            "diagnosis", "priority", "notes",
            "recommended_hospital_id", "applied_funding_id", "assigned_clinician_id",
        )
        return self


class CaseStatusTransitionRequest(BaseModel):
    """PATCH /cases/{id}/status."""

    status: Literal[CASE_STATUS_VALUES]


# ── Response schemas ─────────────────────────────────────


class CaseResponse(BaseModel):
    """Full case record returned by GET /cases/{id}."""

    id: UUID
    patient_id: UUID
    diagnosis: str
    status: str
    priority: str
    notes: str | None
    recommended_hospital_id: UUID | None
    applied_funding_id: UUID | None
    assigned_clinician_id: UUID | None
    created_by: UUID
    closed_at: datetime | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CaseListItem(BaseModel):
    """Subset for list views."""

    id: UUID
    patient_id: UUID
    diagnosis: str
    status: str
    priority: str
    created_by: UUID
    created_at: datetime


class CaseListResponse(BaseModel):
    """Paginated case list."""

    items: list[CaseListItem]
    total: int
    page: int
    per_page: int


class TimelineEventResponse(BaseModel):
    """Single timeline event."""

    id: UUID
    case_id: UUID
    user_id: UUID | None
    event_type: str
    title: str
    description: str | None
    old_value: str | None
    new_value: str | None
    created_at: datetime


class TimelineEventListResponse(BaseModel):
    """List of timeline events."""

    items: list[TimelineEventResponse]


# ── ORM → dict helpers (avoid lazy-load issues) ──────────

# These extract only the schema-relevant columns from ORM objects,
# avoiding Pydantic's from_attributes mode which triggers lazy loads
# on relationships during serialization outside the async context.


def case_to_dict(case: object) -> dict:
    """Convert a Case ORM object to a dict for CaseResponse serialization."""
    return {
        "id": case.id,
        "patient_id": case.patient_id,
        "diagnosis": case.diagnosis,
        "status": case.status,
        "priority": case.priority,
        "notes": case.notes,
        "recommended_hospital_id": case.recommended_hospital_id,
        "applied_funding_id": case.applied_funding_id,
        "assigned_clinician_id": case.assigned_clinician_id,
        "created_by": case.created_by,
        "closed_at": case.closed_at,
        "deleted_at": case.deleted_at,
        "created_at": case.created_at,
        "updated_at": case.updated_at,
    }


def case_list_item_to_dict(case: object) -> dict:
    """Convert a Case ORM object to a dict for CaseListItem serialization."""
    return {
        "id": case.id,
        "patient_id": case.patient_id,
        "diagnosis": case.diagnosis,
        "status": case.status,
        "priority": case.priority,
        "created_by": case.created_by,
        "created_at": case.created_at,
    }


def timeline_event_to_dict(event: object) -> dict:
    """Convert a TimelineEvent ORM object to a dict for TimelineEventResponse."""
    return {
        "id": event.id,
        "case_id": event.case_id,
        "user_id": event.user_id,
        "event_type": event.event_type,
        "title": event.title,
        "description": event.description,
        "old_value": event.old_value,
        "new_value": event.new_value,
        "created_at": event.created_at,
    }
