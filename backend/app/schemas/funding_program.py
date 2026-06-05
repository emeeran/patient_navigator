"""Pydantic schemas for FundingProgram endpoints — DATA-007, API-050..054."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

# ── Request schemas ─────────────────────────────────────


class FundingProgramCreateRequest(BaseModel):
    """Schema for creating a funding program."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    provider: str | None = Field(None, max_length=255)
    program_type: str | None = Field(None, max_length=50)
    eligibility_criteria: str | None = None
    max_amount: float | None = Field(None, ge=0)
    min_amount: float | None = Field(None, ge=0)
    application_url: str | None = Field(None, max_length=500)
    deadline: datetime | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(None, max_length=20)


class FundingProgramUpdateRequest(BaseModel):
    """Schema for updating a funding program — all fields optional."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    provider: str | None = Field(None, max_length=255)
    program_type: str | None = Field(None, max_length=50)
    eligibility_criteria: str | None = None
    max_amount: float | None = Field(None, ge=0)
    min_amount: float | None = Field(None, ge=0)
    application_url: str | None = Field(None, max_length=500)
    deadline: datetime | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(None, max_length=20)


# ── Response schemas ─────────────────────────────────────


class FundingProgramResponse(BaseModel):
    """Full funding program detail."""

    id: UUID
    name: str
    description: str | None
    provider: str | None
    program_type: str | None
    eligibility_criteria: str | None
    max_amount: float | None
    min_amount: float | None
    application_url: str | None
    deadline: datetime | None
    is_active: bool
    contact_email: str | None
    contact_phone: str | None
    created_at: datetime
    updated_at: datetime


class FundingProgramListItem(BaseModel):
    """Subset for list views."""

    id: UUID
    name: str
    provider: str | None
    program_type: str | None
    max_amount: float | None
    min_amount: float | None
    deadline: datetime | None
    is_active: bool
    created_at: datetime


class FundingProgramListResponse(BaseModel):
    """Paginated funding program list."""

    items: list[FundingProgramListItem]
    total: int
    page: int
    per_page: int


# ── ORM -> dict helpers ──────────────────────────────────


def funding_program_to_dict(fp: object) -> dict:
    """Convert a FundingProgram ORM object to a dict for FundingProgramResponse."""
    return {
        "id": fp.id,
        "name": fp.name,
        "description": fp.description,
        "provider": fp.provider,
        "program_type": fp.program_type,
        "eligibility_criteria": fp.eligibility_criteria,
        "max_amount": fp.max_amount,
        "min_amount": fp.min_amount,
        "application_url": fp.application_url,
        "deadline": fp.deadline,
        "is_active": fp.is_active,
        "contact_email": fp.contact_email,
        "contact_phone": fp.contact_phone,
        "created_at": fp.created_at,
        "updated_at": fp.updated_at,
    }


def funding_program_list_item_to_dict(fp: object) -> dict:
    """Convert a FundingProgram ORM object to a dict for FundingProgramListItem."""
    return {
        "id": fp.id,
        "name": fp.name,
        "provider": fp.provider,
        "program_type": fp.program_type,
        "max_amount": fp.max_amount,
        "min_amount": fp.min_amount,
        "deadline": fp.deadline,
        "is_active": fp.is_active,
        "created_at": fp.created_at,
    }


# ── Bulk Import schema ───────────────────────────────────


class NGOImportItem(BaseModel):
    """A single NGO/funding program record for bulk import."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    provider: str | None = Field(None, max_length=255)
    program_type: str | None = Field(None, max_length=50)
    eligibility_criteria: str | None = None
    max_amount: float | None = Field(None, ge=0)
    min_amount: float | None = Field(None, ge=0)
    application_url: str | None = Field(None, max_length=500)
    contact_email: str | None = None
    contact_phone: str | None = Field(None, max_length=20)
