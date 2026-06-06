"""Case endpoints — FEAT-003, API-020..026."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_client_ip, get_current_active_user, require_role
from app.core.database import get_db
from app.models.user import User
from app.schemas.case import (
    CaseCreateRequest,
    CaseListItem,
    CaseListResponse,
    CaseStatusTransitionRequest,
    CaseUpdateRequest,
    TimelineEventListResponse,
    TimelineEventResponse,
    case_list_item_to_dict,
    case_to_dict,
    timeline_event_to_dict,
)
from app.services.case_service import CaseService

router = APIRouter()


# ── Nested under /patients/{patient_id}/cases ───────────


@router.post("/patients/{patient_id}/cases", status_code=201)
async def create_case(
    patient_id: UUID,
    data: CaseCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "navigator")),
):
    """API-021: Create a new case for a patient."""
    service = CaseService(db)
    case = await service.create(
        patient_id=patient_id,
        data=data,
        actor_id=current_user.id,
        ip_address=get_client_ip(request),
    )
    return case_to_dict(case)


@router.get("/patients/{patient_id}/cases")
async def list_cases_for_patient(
    patient_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """API-020: List cases for a specific patient."""
    service = CaseService(db)
    items, total = await service.list_cases_for_patient(
        patient_id=patient_id,
        page=page,
        per_page=per_page,
    )
    return CaseListResponse(
        items=[CaseListItem(**case_list_item_to_dict(c)) for c in items],
        total=total,
        page=page,
        per_page=per_page,
    ).model_dump()


# ── Top-level /cases ────────────────────────────────────


@router.get("/cases")
async def list_all_cases(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    priority: str | None = Query(None),
    sort: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """API-025: List all cases with filters."""
    service = CaseService(db)
    items, total = await service.list_all_cases(
        page=page,
        per_page=per_page,
        status=status,
        priority=priority,
        sort=sort,
    )
    return CaseListResponse(
        items=[CaseListItem(**case_list_item_to_dict(c)) for c in items],
        total=total,
        page=page,
        per_page=per_page,
    ).model_dump()


@router.get("/cases/{case_id}")
async def get_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """API-022: Get case detail by ID."""
    service = CaseService(db)
    case = await service.get_by_id(case_id)
    return case_to_dict(case)


@router.patch("/cases/{case_id}")
async def update_case(
    case_id: UUID,
    data: CaseUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "navigator")),
):
    """API-023: Update case fields."""
    service = CaseService(db)
    case = await service.update(
        case_id=case_id,
        data=data,
        actor_id=current_user.id,
        ip_address=get_client_ip(request),
    )
    return case_to_dict(case)


@router.patch("/cases/{case_id}/status")
async def transition_case_status(
    case_id: UUID,
    data: CaseStatusTransitionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "navigator")),
):
    """API-024: Transition case status through state machine."""
    service = CaseService(db)
    case = await service.transition_status(
        case_id=case_id,
        new_status=data.status,
        actor_id=current_user.id,
        ip_address=get_client_ip(request),
    )
    return case_to_dict(case)


@router.get("/cases/{case_id}/timeline")
async def get_case_timeline(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """API-026: Get timeline events for a case."""
    service = CaseService(db)
    events = await service.get_timeline(case_id)
    return TimelineEventListResponse(
        items=[TimelineEventResponse(**timeline_event_to_dict(e)) for e in events],
    ).model_dump()


@router.delete("/cases/{case_id}", status_code=204)
async def delete_case(
    case_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Soft-delete a case (admin only)."""
    from datetime import UTC, datetime

    service = CaseService(db)
    case = await service.get_by_id(case_id)
    case.deleted_at = datetime.now(UTC)
    await db.flush()
    return None
