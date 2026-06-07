"""Pydantic schemas for MedicalProfile — CRUD + computed BMI."""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.validators import check_at_least_one

# ── Request schemas ─────────────────────────────────────


class MedicalProfileCreateRequest(BaseModel):
    """POST /patients/{id}/medical-profile — at least one field required."""

    date_of_birth: date | None = None
    height_cm: float | None = Field(None, gt=0, le=300)
    weight_kg: float | None = Field(None, gt=0, le=500)
    blood_type: str | None = Field(None, max_length=10)
    past_medical_history: list[str] | None = None
    family_medical_history: list[dict[str, Any]] | None = None
    chronic_conditions: list[str] | None = None
    current_medications: list[str] | None = None
    allergies: list[str] | None = None
    notes: str | None = Field(None, max_length=10000)

    @model_validator(mode="after")
    def at_least_one_field(self) -> "MedicalProfileCreateRequest":
        check_at_least_one(
            self,
            "date_of_birth", "height_cm", "weight_kg", "blood_type",
            "past_medical_history", "family_medical_history", "chronic_conditions",
            "current_medications", "allergies", "notes",
        )
        return self


class MedicalProfileUpdateRequest(BaseModel):
    """PATCH /patients/{id}/medical-profile — at least one field required."""

    date_of_birth: date | None = None
    height_cm: float | None = Field(None, gt=0, le=300)
    weight_kg: float | None = Field(None, gt=0, le=500)
    blood_type: str | None = Field(None, max_length=10)
    past_medical_history: list[str] | None = None
    family_medical_history: list[dict[str, Any]] | None = None
    chronic_conditions: list[str] | None = None
    current_medications: list[str] | None = None
    allergies: list[str] | None = None
    notes: str | None = Field(None, max_length=10000)

    @model_validator(mode="after")
    def at_least_one_field(self) -> "MedicalProfileUpdateRequest":
        check_at_least_one(
            self,
            "date_of_birth", "height_cm", "weight_kg", "blood_type",
            "past_medical_history", "family_medical_history", "chronic_conditions",
            "current_medications", "allergies", "notes",
        )
        return self


# ── Response schema ─────────────────────────────────────


class MedicalProfileResponse(BaseModel):
    """Full medical profile with computed BMI."""

    id: UUID
    patient_id: UUID
    date_of_birth: date | None
    height_cm: float | None
    weight_kg: float | None
    bmi: float | None
    blood_type: str | None
    past_medical_history: list[str] | None
    family_medical_history: list[dict[str, Any]] | None
    chronic_conditions: list[str] | None
    current_medications: list[str] | None
    allergies: list[str] | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


# ── ORM → dict helper ───────────────────────────────────

_MEDICAL_PROFILE_FIELDS = (
    "id",
    "patient_id",
    "date_of_birth",
    "height_cm",
    "weight_kg",
    "blood_type",
    "past_medical_history",
    "family_medical_history",
    "chronic_conditions",
    "current_medications",
    "allergies",
    "notes",
    "created_at",
    "updated_at",
)


def _compute_bmi(height_cm: float | None, weight_kg: float | None) -> float | None:
    """Compute BMI from height (cm) and weight (kg). Returns None if either missing."""
    if height_cm and weight_kg and height_cm > 0:
        height_m = height_cm / 100
        return round(weight_kg / (height_m * height_m), 1)
    return None


def medical_profile_to_dict(profile: object) -> dict:
    """Convert a MedicalProfile ORM object to a response dict (includes computed BMI)."""
    result = {field: getattr(profile, field) for field in _MEDICAL_PROFILE_FIELDS}
    result["bmi"] = _compute_bmi(profile.height_cm, profile.weight_kg)
    return result
