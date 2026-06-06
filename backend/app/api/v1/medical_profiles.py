"""Medical profile endpoints — GET/POST/PATCH per patient."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_client_ip, get_current_active_user, require_role
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.medical_profile import MedicalProfile
from app.models.patient import Patient
from app.models.user import User
from app.schemas.medical_profile import (
    MedicalProfileCreateRequest,
    MedicalProfileUpdateRequest,
    medical_profile_to_dict,
)
from app.services.auth_service import write_audit_log

router = APIRouter(redirect_slashes=False)


async def _get_patient_or_404(db: AsyncSession, patient_id: UUID) -> Patient:
    """Fetch patient or raise 404."""
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise NotFoundError(f"Patient {patient_id} not found")
    return patient


async def _get_profile_or_404(
    db: AsyncSession, patient_id: UUID
) -> MedicalProfile:
    """Fetch medical profile for a patient or raise 404."""
    result = await db.execute(
        select(MedicalProfile).where(MedicalProfile.patient_id == patient_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise NotFoundError("Medical profile not found for this patient")
    return profile


@router.get("/{patient_id}/medical-profile")
async def get_medical_profile(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get the medical profile for a patient."""
    await _get_patient_or_404(db, patient_id)
    profile = await _get_profile_or_404(db, patient_id)
    return medical_profile_to_dict(profile)


@router.post("/{patient_id}/medical-profile", status_code=201)
async def create_medical_profile(
    patient_id: UUID,
    data: MedicalProfileCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "navigator")),
):
    """Create a medical profile for a patient (one per patient)."""
    await _get_patient_or_404(db, patient_id)

    # Check for existing profile
    existing = await db.execute(
        select(MedicalProfile).where(MedicalProfile.patient_id == patient_id)
    )
    if existing.scalar_one_or_none():
        from app.core.exceptions import ConflictError

        raise ConflictError("Medical profile already exists for this patient")

    profile = MedicalProfile(
        patient_id=patient_id,
        date_of_birth=data.date_of_birth,
        height_cm=data.height_cm,
        weight_kg=data.weight_kg,
        blood_type=data.blood_type,
        past_medical_history=data.past_medical_history,
        family_medical_history=data.family_medical_history,
        chronic_conditions=data.chronic_conditions,
        current_medications=data.current_medications,
        allergies=data.allergies,
        notes=data.notes,
    )
    db.add(profile)
    await db.flush()
    await db.refresh(profile)

    await write_audit_log(
        db,
        action="medical_profile.created",
        user_id=current_user.id,
        entity_type="medical_profile",
        entity_id=profile.id,
        description=f"Created medical profile for patient {patient_id}",
        ip_address=get_client_ip(request),
    )

    return medical_profile_to_dict(profile)


@router.patch("/{patient_id}/medical-profile")
async def update_medical_profile(
    patient_id: UUID,
    data: MedicalProfileUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "navigator")),
):
    """Update the medical profile for a patient."""
    await _get_patient_or_404(db, patient_id)
    profile = await _get_profile_or_404(db, patient_id)

    update_fields = data.model_dump(exclude_unset=True, exclude_none=False)
    for field, value in update_fields.items():
        if hasattr(profile, field):
            setattr(profile, field, value)

    await db.flush()
    await db.refresh(profile)

    await write_audit_log(
        db,
        action="medical_profile.updated",
        user_id=current_user.id,
        entity_type="medical_profile",
        entity_id=profile.id,
        description=f"Updated medical profile for patient {patient_id}",
        ip_address=get_client_ip(request),
    )

    return medical_profile_to_dict(profile)
