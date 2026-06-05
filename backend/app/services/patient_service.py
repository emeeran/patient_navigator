"""Patient business logic — CRUD, search, soft-delete, audit — FEAT-002."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ArchivedPatientError, NotFoundError
from app.models.audit_log import AuditLog
from app.models.patient import Patient
from app.schemas.patient import PatientCreateRequest, PatientUpdateRequest


async def _write_audit_log(
    db: AsyncSession,
    *,
    action: str,
    user_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    description: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Write an entry to the audit log."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        ip_address=ip_address,
    )
    db.add(entry)
    await db.flush()
    return entry


class PatientService:
    """Handles all patient CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        data: PatientCreateRequest,
        actor_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Patient:
        """Create a new patient record. Returns the created Patient."""
        patient = Patient(
            full_name=data.full_name,
            age=data.age,
            gender=data.gender,
            phone=data.phone,
            email=data.email,
            address=data.address,
            emergency_contact_name=data.emergency_contact_name,
            emergency_contact_phone=data.emergency_contact_phone,
            notes=data.notes,
            navigator_id=data.navigator_id,
            created_by=actor_id,
            status="active",
        )
        self.db.add(patient)
        await self.db.flush()
        await self.db.refresh(patient)

        await _write_audit_log(
            self.db,
            action="patient.created",
            user_id=actor_id,
            entity_type="patient",
            entity_id=patient.id,
            description=f"Created patient {patient.full_name}",
            ip_address=ip_address,
        )
        return patient

    async def get_by_id(self, patient_id: uuid.UUID) -> Patient:
        """Get a patient by ID. Raises NotFoundError if not found."""
        result = await self.db.execute(
            select(Patient).where(Patient.id == patient_id)
        )
        patient = result.scalar_one_or_none()
        if not patient:
            raise NotFoundError(f"Patient {patient_id} not found")
        return patient

    async def list_patients(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        status: str | None = None,
        sort: str | None = None,
    ) -> tuple[list[Patient], int]:
        """List patients with optional search, filter, sort, and pagination.

        Returns (items, total_count).
        By default excludes archived patients (soft-deleted).
        """
        # Base query: exclude archived unless explicitly requested
        base_filter = Patient.deleted_at.is_(None)
        if status == "archived":
            base_filter = Patient.deleted_at.isnot(None)
        elif status:
            base_filter = (Patient.deleted_at.is_(None)) & (Patient.status == status)

        # Count query
        count_q = select(func.count()).select_from(Patient).where(base_filter)
        if search:
            count_q = count_q.where(
                Patient.full_name.op("%")(search)  # trigram LIKE
            )

        total_result = await self.db.execute(count_q)
        total = total_result.scalar() or 0

        # Data query
        data_q: Select = select(Patient).where(base_filter)
        if search:
            data_q = data_q.where(Patient.full_name.op("%")(search))

        # Sorting
        if sort:
            desc = sort.startswith("-")
            col_name = sort.lstrip("-")
            col = getattr(Patient, col_name, None)
            if col is not None:
                data_q = data_q.order_by(col.desc() if desc else col.asc())
        else:
            data_q = data_q.order_by(Patient.created_at.desc())

        # Pagination
        offset = (page - 1) * per_page
        data_q = data_q.offset(offset).limit(per_page)

        result = await self.db.execute(data_q)
        items = list(result.scalars().all())
        return items, total

    async def update(
        self,
        patient_id: uuid.UUID,
        data: PatientUpdateRequest,
        actor_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Patient:
        """Update patient fields. Raises ArchivedPatientError if archived."""
        patient = await self.get_by_id(patient_id)
        if patient.deleted_at is not None:
            raise ArchivedPatientError()

        update_fields = data.model_dump(exclude_unset=True, exclude_none=False)
        for field, value in update_fields.items():
            if hasattr(patient, field):
                setattr(patient, field, value)

        await self.db.flush()
        await self.db.refresh(patient)

        await _write_audit_log(
            self.db,
            action="patient.updated",
            user_id=actor_id,
            entity_type="patient",
            entity_id=patient.id,
            description=f"Updated patient {patient.full_name}",
            ip_address=ip_address,
        )
        return patient

    async def archive(
        self,
        patient_id: uuid.UUID,
        actor_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> None:
        """Soft-delete (archive) a patient."""
        patient = await self.get_by_id(patient_id)
        if patient.deleted_at is not None:
            raise ArchivedPatientError("Patient is already archived")

        patient.deleted_at = datetime.now(UTC)
        patient.status = "archived"
        await self.db.flush()

        await _write_audit_log(
            self.db,
            action="patient.archived",
            user_id=actor_id,
            entity_type="patient",
            entity_id=patient.id,
            description=f"Archived patient {patient.full_name}",
            ip_address=ip_address,
        )
