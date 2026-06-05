"""Funding program endpoints — FEAT-007, API-050..054."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_role
from app.core.database import get_db
from app.models.user import User
from app.schemas.funding_program import (
    FundingProgramCreateRequest,
    FundingProgramListItem,
    FundingProgramListResponse,
    FundingProgramResponse,
    FundingProgramUpdateRequest,
    funding_program_list_item_to_dict,
    funding_program_to_dict,
)
from app.services.funding_service import FundingService

router = APIRouter()


@router.get("/funding")
async def list_funding_programs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    is_active: bool | None = Query(None),
    sort: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """API-050: List funding programs with optional filters and search."""
    service = FundingService(db)
    items, total = await service.list_programs(
        page=page,
        per_page=per_page,
        search=search,
        is_active=is_active,
        sort=sort,
    )
    return FundingProgramListResponse(
        items=[FundingProgramListItem(**funding_program_list_item_to_dict(fp)) for fp in items],
        total=total,
        page=page,
        per_page=per_page,
    ).model_dump()


@router.get("/funding/{program_id}")
async def get_funding_program(
    program_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """API-051: Get funding program detail."""
    service = FundingService(db)
    program = await service.get_by_id(program_id)
    return FundingProgramResponse(**funding_program_to_dict(program)).model_dump()


@router.post("/funding", status_code=201)
async def create_funding_program(
    payload: FundingProgramCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """API-052: Create a funding program (admin only)."""
    service = FundingService(db)
    program = await service.create(payload.model_dump())
    return FundingProgramResponse(**funding_program_to_dict(program)).model_dump()


@router.patch("/funding/{program_id}")
async def update_funding_program(
    program_id: uuid.UUID,
    payload: FundingProgramUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """API-053: Update a funding program (admin only)."""
    service = FundingService(db)
    program = await service.update(program_id, payload)
    return FundingProgramResponse(**funding_program_to_dict(program)).model_dump()


@router.delete("/funding/{program_id}", status_code=204)
async def archive_funding_program(
    program_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """API-054: Archive (soft-delete) a funding program (admin only)."""
    service = FundingService(db)
    await service.archive(program_id)
    return None
