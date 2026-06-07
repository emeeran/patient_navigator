"""Pydantic schemas for Patient endpoints — DATA-003, API-010..014."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.schemas.validators import check_at_least_one

# ── Enums ──────────────────────────────────────────────
GENDER_VALUES = ("male", "female", "other", "prefer_not_to_say")
PATIENT_STATUS_VALUES = ("active", "inactive", "archived")


# ── Request schemas ─────────────────────────────────────


class PatientCreateRequest(BaseModel):
    """POST /patients — all required PII fields, optional contact info."""

    full_name: str = Field(..., min_length=1, max_length=255)
    age: int = Field(..., ge=0, le=150)
    gender: Literal[GENDER_VALUES]
    phone: str | None = Field(None, max_length=20)
    email: EmailStr | None = None
    address: str | None = Field(None, max_length=1000)
    emergency_contact_name: str | None = Field(None, max_length=255)
    emergency_contact_phone: str | None = Field(None, max_length=20)
    notes: str | None = Field(None, max_length=10000)
    navigator_id: UUID | None = None


class PatientUpdateRequest(BaseModel):
    """PATCH /patients/{id} — at least one field required."""

    full_name: str | None = Field(None, min_length=1, max_length=255)
    age: int | None = Field(None, ge=0, le=150)
    gender: Literal[GENDER_VALUES] | None = None
    phone: str | None = Field(None, max_length=20)
    email: EmailStr | None = None
    address: str | None = Field(None, max_length=1000)
    emergency_contact_name: str | None = Field(None, max_length=255)
    emergency_contact_phone: str | None = Field(None, max_length=20)
    notes: str | None = Field(None, max_length=10000)
    navigator_id: UUID | None = None
    status: Literal[PATIENT_STATUS_VALUES] | None = None

    @model_validator(mode="after")
    def at_least_one_field(self):
        check_at_least_one(
            self,
            "full_name", "age", "gender", "phone", "email", "address",
            "emergency_contact_name", "emergency_contact_phone",
            "notes", "navigator_id", "status",
        )
        return self


# ── Response schemas ─────────────────────────────────────


class PatientResponse(BaseModel):
    """Full patient record returned by GET /patients/{id}."""

    id: UUID
    full_name: str
    age: int
    gender: str
    phone: str | None
    email: str | None
    address: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    navigator_id: UUID | None
    status: str
    notes: str | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    medical_profile: dict[str, Any] | None = None


class PatientListItem(BaseModel):
    """Subset for list views — GET /patients."""

    id: UUID
    full_name: str
    age: int
    gender: str
    status: str
    navigator_id: UUID | None
    created_at: datetime


class PatientListResponse(BaseModel):
    """Paginated patient list."""

    items: list[PatientListItem]
    total: int
    page: int
    per_page: int


# ── ORM → dict helpers (avoid lazy-load issues) ──────────

# These extract only the schema-relevant columns from ORM objects,
# avoiding Pydantic's from_attributes mode which triggers lazy loads
# on relationships during serialization outside the async context.


def patient_to_dict(patient: object) -> dict:
    """Convert a Patient ORM object to a dict for PatientResponse serialization."""
    from app.schemas.medical_profile import medical_profile_to_dict

    result = {
        "id": patient.id,
        "full_name": patient.full_name,
        "age": patient.age,
        "gender": patient.gender,
        "phone": patient.phone,
        "email": patient.email,
        "address": patient.address,
        "emergency_contact_name": patient.emergency_contact_name,
        "emergency_contact_phone": patient.emergency_contact_phone,
        "navigator_id": patient.navigator_id,
        "status": patient.status,
        "notes": patient.notes,
        "created_by": patient.created_by,
        "created_at": patient.created_at,
        "updated_at": patient.updated_at,
        "deleted_at": patient.deleted_at,
    }
    if hasattr(patient, "medical_profile") and patient.medical_profile is not None:
        result["medical_profile"] = medical_profile_to_dict(patient.medical_profile)
    else:
        result["medical_profile"] = None
    return result


def patient_list_item_to_dict(patient: object) -> dict:
    """Convert a Patient ORM object to a dict for PatientListItem serialization."""
    return {
        "id": patient.id,
        "full_name": patient.full_name,
        "age": patient.age,
        "gender": patient.gender,
        "status": patient.status,
        "navigator_id": patient.navigator_id,
        "created_at": patient.created_at,
    }
