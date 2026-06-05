"""Follow-Up Tracking endpoints — FEAT-008, API-060..067."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_role
from app.core.database import get_db
from app.models.user import User
from app.schemas.follow_up import (
    FollowUpCreateRequest,
    FollowUpListItem,
    FollowUpListResponse,
    FollowUpUpdateRequest,
    follow_up_list_item_to_dict,
    follow_up_to_dict,
)
from app.services.follow_up_service import FollowUpService

router = APIRouter()


@router.post("/cases/{case_id}/followups", status_code=201)
async def create_follow_up(
    case_id: uuid.UUID,
    data: FollowUpCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "navigator")),
):
    """API-060: Schedule a new follow-up for a case."""
    service = FollowUpService(db)
    fu = await service.create(case_id, data, created_by=current_user.id)
    return follow_up_to_dict(fu)


@router.get("/cases/{case_id}/followups")
async def list_case_follow_ups(
    case_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """API-061: List follow-ups for a case."""
    service = FollowUpService(db)
    items, total = await service.list_for_case(case_id, page, per_page, status)
    return FollowUpListResponse(
        items=[FollowUpListItem(**follow_up_list_item_to_dict(f)) for f in items],
        total=total,
        page=page,
        per_page=per_page,
    ).model_dump()


@router.get("/followups/upcoming")
async def list_upcoming_follow_ups(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    type: str | None = Query(None, alias="type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """API-062: List all upcoming follow-ups."""
    service = FollowUpService(db)
    items, total = await service.list_upcoming(page, per_page, follow_up_type=type)
    return FollowUpListResponse(
        items=[FollowUpListItem(**follow_up_list_item_to_dict(f)) for f in items],
        total=total,
        page=page,
        per_page=per_page,
    ).model_dump()


@router.get("/followups/{follow_up_id}")
async def get_follow_up(
    follow_up_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """API-063: Get follow-up detail."""
    service = FollowUpService(db)
    fu = await service.get_by_id(follow_up_id)
    return follow_up_to_dict(fu)


@router.put("/followups/{follow_up_id}")
async def update_follow_up(
    follow_up_id: uuid.UUID,
    data: FollowUpUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "navigator")),
):
    """API-064: Update a follow-up."""
    service = FollowUpService(db)
    fu = await service.update(follow_up_id, data)
    return follow_up_to_dict(fu)


@router.patch("/followups/{follow_up_id}")
async def patch_follow_up(
    follow_up_id: uuid.UUID,
    data: FollowUpUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "navigator")),
):
    """API-065: Partially update a follow-up (status changes)."""
    service = FollowUpService(db)
    fu = await service.update(follow_up_id, data)
    return follow_up_to_dict(fu)


@router.post("/followups/{follow_up_id}/complete")
async def complete_follow_up(
    follow_up_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "navigator")),
):
    """API-066: Mark follow-up as completed."""
    service = FollowUpService(db)
    fu = await service.complete(follow_up_id, completed_by=current_user.id)
    return follow_up_to_dict(fu)
