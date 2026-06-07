"""Pydantic schemas for Doctor Directory."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.validators import check_at_least_one


class DoctorCreateRequest(BaseModel):
    """Create a new doctor."""

    name: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str | None = Field(None, max_length=100)
    address: str | None = Field(None, max_length=500)
    phone: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=254)
    website: str | None = Field(None, max_length=500)
    specialty: str | None = Field(None, max_length=255)
    qualification: str | None = Field(None, max_length=255)
    registration_number: str | None = Field(None, max_length=100)
    medical_council: str | None = Field(None, max_length=255)
    hospital_name: str | None = Field(None, max_length=255)
    practice_type: str | None = Field(None, max_length=50)
    latitude: float | None = None
    longitude: float | None = None


class DoctorUpdateRequest(BaseModel):
    """Update a doctor — at least one field required."""

    name: str | None = Field(None, min_length=1, max_length=255)
    city: str | None = Field(None, min_length=1, max_length=100)
    state: str | None = Field(None, max_length=100)
    address: str | None = Field(None, max_length=500)
    phone: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=254)
    website: str | None = Field(None, max_length=500)
    specialty: str | None = Field(None, max_length=255)
    qualification: str | None = Field(None, max_length=255)
    registration_number: str | None = Field(None, max_length=100)
    medical_council: str | None = Field(None, max_length=255)
    hospital_name: str | None = Field(None, max_length=255)
    practice_type: str | None = Field(None, max_length=50)
    is_active: bool | None = None
    latitude: float | None = None
    longitude: float | None = None

    @model_validator(mode="after")
    def validate_fields(self):
        check_at_least_one(
            self,
            "name", "city", "state", "address", "phone", "email", "website",
            "specialty", "qualification", "registration_number", "medical_council",
            "hospital_name", "practice_type", "is_active", "latitude", "longitude",
        )
        return self


class DoctorResponse(BaseModel):
    """Full doctor response."""

    id: UUID
    name: str
    city: str
    state: str | None
    address: str | None
    phone: str | None
    email: str | None
    website: str | None
    specialty: str | None
    qualification: str | None
    registration_number: str | None
    medical_council: str | None
    hospital_name: str | None
    practice_type: str | None
    is_active: bool
    latitude: float | None
    longitude: float | None
    created_at: datetime
    updated_at: datetime


class DoctorListItem(BaseModel):
    """Doctor list item."""

    id: UUID
    name: str
    city: str
    specialty: str | None
    qualification: str | None
    practice_type: str | None
    hospital_name: str | None
    is_active: bool
    created_at: datetime


class DoctorListResponse(BaseModel):
    """Paginated doctor list."""

    items: list[DoctorListItem]
    total: int
    page: int
    per_page: int


# ── ORM → dict helpers ──────────────────────────────────


def doctor_to_dict(d: object) -> dict:
    """Convert a Doctor ORM object to a full response dict."""
    return {
        "id": d.id,
        "name": d.name,
        "city": d.city,
        "state": d.state,
        "address": d.address,
        "phone": d.phone,
        "email": d.email,
        "website": d.website,
        "specialty": d.specialty,
        "qualification": d.qualification,
        "registration_number": d.registration_number,
        "medical_council": d.medical_council,
        "hospital_name": d.hospital_name,
        "practice_type": d.practice_type,
        "is_active": d.is_active,
        "latitude": d.latitude,
        "longitude": d.longitude,
        "created_at": d.created_at,
        "updated_at": d.updated_at,
    }


def doctor_list_item_to_dict(d: object) -> dict:
    """Convert a Doctor ORM to a list item dict."""
    return {
        "id": d.id,
        "name": d.name,
        "city": d.city,
        "specialty": d.specialty,
        "qualification": d.qualification,
        "practice_type": d.practice_type,
        "hospital_name": d.hospital_name,
        "is_active": d.is_active,
        "created_at": d.created_at,
    }
