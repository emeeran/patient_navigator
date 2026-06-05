"""AI and Clinician Review endpoints — FEAT-005, API-040..048."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_role
from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.models.medical_summary import ClinicianReview
from app.models.user import User
from app.schemas.medical_summary import (
    ExplainRequest,
    QuestionsForDoctorRequest,
    ReviewCreateRequest,
    ReviewListItem,
    ReviewListResponse,
    ReviewUpdateRequest,
    SuggestSpecialistRequest,
    SummarizeRequest,
    review_list_item_to_dict,
    review_to_dict,
)
from app.services.ai_service import AIService

router = APIRouter()


# ── AI endpoints ────────────────────────────────────────


@router.post("/ai/summarize")
async def summarize(
    data: SummarizeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "navigator", "clinician")),
):
    """API-040: Generate AI medical summary for a case."""
    service = AIService(db)
    return await service.summarize_case(
        case_id=data.case_id, document_ids=data.document_ids
    )


@router.post("/ai/explain")
async def explain(
    data: ExplainRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "navigator", "clinician")),
):
    """API-041: Explain medical terms in plain language."""
    service = AIService(db)
    return await service.explain_terms(text=data.text)


@router.post("/ai/suggest-specialist")
async def suggest_specialist(
    data: SuggestSpecialistRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "navigator")),
):
    """API-042: Suggest specialist type based on case."""
    service = AIService(db)
    return await service.suggest_specialist(
        case_id=data.case_id, diagnosis=data.diagnosis
    )


@router.post("/ai/questions-for-doctor")
async def questions_for_doctor(
    data: QuestionsForDoctorRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "navigator")),
):
    """API-043: Generate questions for the doctor."""
    service = AIService(db)
    return await service.generate_questions(
        case_id=data.case_id, context=data.context
    )


# ── Clinician Review endpoints ──────────────────────────


@router.post("/cases/{case_id}/reviews", status_code=201)
async def create_review(
    case_id: uuid.UUID,
    data: ReviewCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "clinician")),
):
    """API-044: Create a clinician review for a case."""
    review = ClinicianReview(
        case_id=case_id,
        reviewer_id=current_user.id,
        summary_text=data.summary_text,
        ai_disclaimer_acknowledged=data.ai_disclaimer_acknowledged,
        status="draft",
    )
    db.add(review)
    await db.flush()
    return review_to_dict(review)


@router.get("/cases/{case_id}/reviews")
async def list_reviews(
    case_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """API-045: List reviews for a case."""
    base_query = select(ClinicianReview).where(
        ClinicianReview.case_id == case_id
    )

    count_q = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = (
        base_query.order_by(ClinicianReview.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    items = result.scalars().all()

    return ReviewListResponse(
        items=[ReviewListItem(**review_list_item_to_dict(r)) for r in items],
        total=total,
        page=page,
        per_page=per_page,
    ).model_dump()


@router.patch("/reviews/{review_id}")
async def update_review(
    review_id: uuid.UUID,
    data: ReviewUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "clinician")),
):
    """API-046: Update review status (approve/reject)."""
    result = await db.execute(
        select(ClinicianReview).where(ClinicianReview.id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise NotFoundError("Review not found")

    if data.status not in ("approved", "rejected"):
        raise ValidationError("Status must be 'approved' or 'rejected'")

    review.status = data.status
    if data.reviewer_comments is not None:
        review.reviewer_comments = data.reviewer_comments
    review.reviewed_at = datetime.now(UTC)
    review.reviewer_id = current_user.id
    await db.flush()

    return review_to_dict(review)
