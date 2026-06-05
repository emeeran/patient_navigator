"""Patient endpoints — FEAT-002, API-010..014."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_role
from app.core.database import get_db
from app.models.user import User
from app.schemas.patient import (
    PatientCreateRequest,
    PatientListItem,
    PatientListResponse,
    PatientUpdateRequest,
    patient_list_item_to_dict,
    patient_to_dict,
)
from app.services.patient_service import PatientService
from app.services.pii_masking import mask_patient_response

router = APIRouter(redirect_slashes=False)


@router.post("", status_code=201)
async def create_patient(
    data: PatientCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "navigator")),
):
    """API-011: Create a new patient record."""
    service = PatientService(db)
    patient = await service.create(
        data,
        actor_id=current_user.id,
        ip_address=_get_ip(request),
    )
    return patient_to_dict(patient)


@router.get("")
async def list_patients(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    status: str | None = Query(None),
    sort: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """API-010: List patients with pagination, search, and filters."""
    service = PatientService(db)
    items, total = await service.list_patients(
        page=page,
        per_page=per_page,
        search=search,
        status=status,
        sort=sort,
    )
    return PatientListResponse(
        items=[PatientListItem(**patient_list_item_to_dict(p)) for p in items],
        total=total,
        page=page,
        per_page=per_page,
    ).model_dump()


@router.get("/{patient_id}")
async def get_patient(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """API-012: Get patient by ID. PII masked based on role."""
    service = PatientService(db)
    patient = await service.get_by_id(patient_id)

    response_data = patient_to_dict(patient)

    # Apply PII masking based on viewer role
    role = current_user.role.name if current_user.role else "volunteer"
    response_data = mask_patient_response(response_data, role)

    return response_data


@router.patch("/{patient_id}")
async def update_patient(
    patient_id: UUID,
    data: PatientUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "navigator")),
):
    """API-013: Update patient information."""
    service = PatientService(db)
    patient = await service.update(
        patient_id,
        data,
        actor_id=current_user.id,
        ip_address=_get_ip(request),
    )
    return patient_to_dict(patient)


@router.delete("/{patient_id}", status_code=204)
async def archive_patient(
    patient_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "navigator")),
):
    """API-014: Archive (soft delete) a patient."""
    service = PatientService(db)
    await service.archive(
        patient_id,
        actor_id=current_user.id,
        ip_address=_get_ip(request),
    )
    return None


def _get_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
