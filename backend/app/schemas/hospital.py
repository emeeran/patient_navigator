"""Pydantic schemas for Hospital Directory — FEAT-006."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class HospitalCreateRequest(BaseModel):
    """Create a new hospital."""

    name: str
    city: str
    state: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    specialties: str | None = None
    has_financial_assistance: bool = False
    rating: float | None = Field(default=None, ge=0, le=5)
    latitude: float | None = None
    longitude: float | None = None


class HospitalUpdateRequest(BaseModel):
    """Update a hospital."""

    name: str | None = None
    city: str | None = None
    state: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    specialties: str | None = None
    has_financial_assistance: bool | None = None
    rating: float | None = Field(default=None, ge=0, le=5)
    is_active: bool | None = None
    latitude: float | None = None
    longitude: float | None = None


class HospitalResponse(BaseModel):
    """Full hospital response."""

    id: UUID
    name: str
    city: str
    state: str | None
    address: str | None
    phone: str | None
    email: str | None
    website: str | None
    specialties: str | None
    has_financial_assistance: bool
    rating: float | None
    is_active: bool
    latitude: float | None
    longitude: float | None
    created_at: datetime
    updated_at: datetime


class HospitalListItem(BaseModel):
    """Hospital list item."""

    id: UUID
    name: str
    city: str
    specialties: str | None
    has_financial_assistance: bool
    rating: float | None
    is_active: bool
    created_at: datetime


class HospitalListResponse(BaseModel):
    """Paginated hospital list."""

    items: list[HospitalListItem]
    total: int
    page: int
    per_page: int


# ── ORM → dict helpers ──────────────────────────────────


def hospital_to_dict(h: object) -> dict:
    """Convert a Hospital ORM object to a full response dict."""
    return {
        "id": h.id,
        "name": h.name,
        "city": h.city,
        "state": h.state,
        "address": h.address,
        "phone": h.phone,
        "email": h.email,
        "website": h.website,
        "specialties": h.specialties,
        "has_financial_assistance": h.has_financial_assistance,
        "rating": h.rating,
        "is_active": h.is_active,
        "latitude": h.latitude,
        "longitude": h.longitude,
        "created_at": h.created_at,
        "updated_at": h.updated_at,
    }


def hospital_list_item_to_dict(h: object) -> dict:
    """Convert a Hospital ORM to a list item dict."""
    return {
        "id": h.id,
        "name": h.name,
        "city": h.city,
        "specialties": h.specialties,
        "has_financial_assistance": h.has_financial_assistance,
        "rating": h.rating,
        "is_active": h.is_active,
        "created_at": h.created_at,
    }
