"""Pydantic schemas for AI Medical Summary and Clinician Review — FEAT-005."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

# ── AI Request schemas ──────────────────────────────────


class SummarizeRequest(BaseModel):
    """Request body for AI summarization."""

    case_id: UUID
    document_ids: list[UUID] | None = None


class ExplainRequest(BaseModel):
    """Request body for medical term explanation."""

    text: str


class SuggestSpecialistRequest(BaseModel):
    """Request body for specialist suggestion."""

    case_id: UUID
    diagnosis: str | None = None


class QuestionsForDoctorRequest(BaseModel):
    """Request body for generating questions for the doctor."""

    case_id: UUID
    context: str | None = None


# ── AI Response schemas ─────────────────────────────────


class AIResponse(BaseModel):
    """Generic AI response with disclaimer."""

    content: str
    disclaimer: str = (
        "This AI-generated content is for informational purposes only. "
        "It must be reviewed and approved by a qualified clinician before "
        "being used for any medical decisions."
    )
    model: str | None = None


# ── Clinician Review schemas ────────────────────────────


class ReviewCreateRequest(BaseModel):
    """Create a new clinician review."""

    summary_text: str
    ai_disclaimer_acknowledged: bool = False


class ReviewUpdateRequest(BaseModel):
    """Update review status (approve/reject)."""

    status: str  # approved, rejected
    reviewer_comments: str | None = None


class ReviewResponse(BaseModel):
    """Full review response."""

    id: UUID
    case_id: UUID
    reviewer_id: UUID
    summary_text: str
    ai_disclaimer_acknowledged: bool
    status: str
    reviewer_comments: str | None
    reviewed_at: datetime | None
    created_at: datetime


class ReviewListItem(BaseModel):
    """Review list item."""

    id: UUID
    case_id: UUID
    reviewer_id: UUID
    status: str
    created_at: datetime
    reviewed_at: datetime | None


class ReviewListResponse(BaseModel):
    """Paginated review list."""

    items: list[ReviewListItem]
    total: int
    page: int
    per_page: int


# ── ORM → dict helpers ──────────────────────────────────


def review_to_dict(review: object) -> dict:
    """Convert a ClinicianReview ORM object to a dict."""
    return {
        "id": review.id,
        "case_id": review.case_id,
        "reviewer_id": review.reviewer_id,
        "summary_text": review.summary_text,
        "ai_disclaimer_acknowledged": review.ai_disclaimer_acknowledged,
        "status": review.status,
        "reviewer_comments": review.reviewer_comments,
        "reviewed_at": review.reviewed_at,
        "created_at": review.created_at,
    }


def review_list_item_to_dict(review: object) -> dict:
    """Convert a ClinicianReview ORM to a list item dict."""
    return {
        "id": review.id,
        "case_id": review.case_id,
        "reviewer_id": review.reviewer_id,
        "status": review.status,
        "created_at": review.created_at,
        "reviewed_at": review.reviewed_at,
    }
