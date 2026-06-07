"""Doctor directory endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_role
from app.core.database import get_db
from app.models.user import User
from app.schemas.doctor import (
    DoctorCreateRequest,
    DoctorListItem,
    DoctorListResponse,
    DoctorUpdateRequest,
    doctor_list_item_to_dict,
    doctor_to_dict,
)
from app.services.doctor_service import DoctorService

router = APIRouter()


@router.get("/doctors")
async def list_doctors(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    city: str | None = Query(None),
    specialty: str | None = Query(None),
    practice_type: str | None = Query(None),
    sort: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List doctors with filters and pagination."""
    service = DoctorService(db)
    items, total = await service.list_doctors(
        page=page,
        per_page=per_page,
        search=search,
        city=city,
        specialty=specialty,
        practice_type=practice_type,
        sort=sort,
    )
    return DoctorListResponse(
        items=[DoctorListItem(**doctor_list_item_to_dict(d)) for d in items],
        total=total,
        page=page,
        per_page=per_page,
    ).model_dump()


@router.get("/doctors/{doctor_id}")
async def get_doctor(
    doctor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get doctor detail."""
    service = DoctorService(db)
    doctor = await service.get_by_id(doctor_id)
    return doctor_to_dict(doctor)


@router.post("/doctors", status_code=201)
async def create_doctor(
    data: DoctorCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Create a new doctor (admin only)."""
    service = DoctorService(db)
    doctor = await service.create(data)
    return doctor_to_dict(doctor)


@router.put("/doctors/{doctor_id}")
async def update_doctor(
    doctor_id: uuid.UUID,
    data: DoctorUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Update a doctor (admin only)."""
    service = DoctorService(db)
    doctor = await service.update(doctor_id, data)
    return doctor_to_dict(doctor)


@router.delete("/doctors/{doctor_id}", status_code=204)
async def archive_doctor(
    doctor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Archive (soft delete) a doctor (admin only)."""
    service = DoctorService(db)
    await service.archive(doctor_id)
    return None
