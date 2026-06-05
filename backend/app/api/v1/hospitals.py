"""Hospital Directory endpoints — FEAT-006, API-050..056."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_role
from app.core.database import get_db
from app.models.user import User
from app.schemas.hospital import (
    HospitalCreateRequest,
    HospitalListItem,
    HospitalListResponse,
    HospitalUpdateRequest,
    hospital_list_item_to_dict,
    hospital_to_dict,
)
from app.services.hospital_service import HospitalService

router = APIRouter()


@router.get("/hospitals")
async def list_hospitals(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    city: str | None = Query(None),
    specialty: str | None = Query(None),
    has_financial_assistance: bool | None = Query(None),
    is_active: bool | None = Query(True),
    sort: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """API-050: List hospitals with filters."""
    service = HospitalService(db)
    items, total = await service.list_hospitals(
        page=page,
        per_page=per_page,
        search=search,
        city=city,
        specialty=specialty,
        has_financial_assistance=has_financial_assistance,
        is_active=is_active,
        sort=sort,
    )
    return HospitalListResponse(
        items=[HospitalListItem(**hospital_list_item_to_dict(h)) for h in items],
        total=total,
        page=page,
        per_page=per_page,
    ).model_dump()


@router.get("/hospitals/{hospital_id}")
async def get_hospital(
    hospital_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """API-051: Get hospital detail."""
    service = HospitalService(db)
    hospital = await service.get_by_id(hospital_id)
    return hospital_to_dict(hospital)


@router.post("/hospitals", status_code=201)
async def create_hospital(
    data: HospitalCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """API-052: Create a new hospital (admin only)."""
    service = HospitalService(db)
    hospital = await service.create(data)
    return hospital_to_dict(hospital)


@router.put("/hospitals/{hospital_id}")
async def update_hospital(
    hospital_id: uuid.UUID,
    data: HospitalUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """API-053: Update hospital (admin only)."""
    service = HospitalService(db)
    hospital = await service.update(hospital_id, data)
    return hospital_to_dict(hospital)


@router.delete("/hospitals/{hospital_id}", status_code=204)
async def archive_hospital(
    hospital_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """API-054: Archive hospital (admin only)."""
    service = HospitalService(db)
    await service.archive(hospital_id)
    return None
