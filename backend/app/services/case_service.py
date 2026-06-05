"""Case business logic — CRUD, state machine, timeline events — FEAT-003."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ArchivedPatientError,
    NotFoundError,
)
from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.timeline_event import TimelineEvent
from app.schemas.case import CaseCreateRequest, CaseUpdateRequest
from app.services.state_machine import validate_transition


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


async def _write_timeline_event(
    db: AsyncSession,
    *,
    case_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
    event_type: str,
    title: str,
    description: str | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
) -> TimelineEvent:
    """Write a timeline event for a case mutation."""
    event = TimelineEvent(
        case_id=case_id,
        user_id=user_id,
        event_type=event_type,
        title=title,
        description=description,
        old_value=old_value,
        new_value=new_value,
    )
    db.add(event)
    await db.flush()
    return event


class CaseService:
    """Handles all case CRUD and state machine operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        patient_id: uuid.UUID,
        data: CaseCreateRequest,
        actor_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Case:
        """Create a new case for a patient."""
        # Verify patient exists and is not archived
        from app.models.patient import Patient

        pat_result = await self.db.execute(
            select(Patient).where(Patient.id == patient_id)
        )
        patient = pat_result.scalar_one_or_none()
        if not patient:
            raise NotFoundError(f"Patient {patient_id} not found")
        if patient.deleted_at is not None:
            raise ArchivedPatientError("Cannot create case for archived patient")

        case = Case(
            patient_id=patient_id,
            diagnosis=data.diagnosis,
            priority=data.priority,
            notes=data.notes,
            recommended_hospital_id=data.recommended_hospital_id,
            applied_funding_id=data.applied_funding_id,
            assigned_clinician_id=data.assigned_clinician_id,
            created_by=actor_id,
            status="new",
        )
        self.db.add(case)
        await self.db.flush()
        await self.db.refresh(case)

        await _write_timeline_event(
            self.db,
            case_id=case.id,
            user_id=actor_id,
            event_type="case.created",
            title="Case created",
            description=f"New case created with diagnosis: {data.diagnosis[:100]}",
            new_value="new",
        )

        await _write_audit_log(
            self.db,
            action="case.created",
            user_id=actor_id,
            entity_type="case",
            entity_id=case.id,
            description=f"Created case for patient {patient_id}",
            ip_address=ip_address,
        )
        return case

    async def get_by_id(self, case_id: uuid.UUID) -> Case:
        """Get a case by ID. Raises NotFoundError if not found."""
        result = await self.db.execute(select(Case).where(Case.id == case_id))
        case = result.scalar_one_or_none()
        if not case:
            raise NotFoundError(f"Case {case_id} not found")
        return case

    async def list_cases_for_patient(
        self,
        patient_id: uuid.UUID,
        *,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Case], int]:
        """List cases for a specific patient, excluding soft-deleted."""
        base = (Case.patient_id == patient_id) & (Case.deleted_at.is_(None))

        total_result = await self.db.execute(
            select(func.count()).select_from(Case).where(base)
        )
        total = total_result.scalar() or 0

        offset = (page - 1) * per_page
        data_q = (
            select(Case)
            .where(base)
            .order_by(Case.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await self.db.execute(data_q)
        items = list(result.scalars().all())
        return items, total

    async def list_all_cases(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        status: str | None = None,
        priority: str | None = None,
        sort: str | None = None,
    ) -> tuple[list[Case], int]:
        """List all cases across patients with optional filters."""
        base = Case.deleted_at.is_(None)
        if status:
            base = base & (Case.status == status)
        if priority:
            base = base & (Case.priority == priority)

        total_result = await self.db.execute(
            select(func.count()).select_from(Case).where(base)
        )
        total = total_result.scalar() or 0

        data_q: Select = select(Case).where(base)

        # Sorting
        if sort:
            desc = sort.startswith("-")
            col_name = sort.lstrip("-")
            col = getattr(Case, col_name, None)
            if col is not None:
                data_q = data_q.order_by(col.desc() if desc else col.asc())
        else:
            data_q = data_q.order_by(Case.created_at.desc())

        offset = (page - 1) * per_page
        data_q = data_q.offset(offset).limit(per_page)

        result = await self.db.execute(data_q)
        items = list(result.scalars().all())
        return items, total

    async def update(
        self,
        case_id: uuid.UUID,
        data: CaseUpdateRequest,
        actor_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Case:
        """Update case fields (diagnosis, priority, notes, etc.)."""
        case = await self.get_by_id(case_id)

        update_fields = data.model_dump(exclude_unset=True, exclude_none=False)
        changed: list[str] = []
        for field, value in update_fields.items():
            if hasattr(case, field) and getattr(case, field) != value:
                changed.append(field)
                setattr(case, field, value)

        await self.db.flush()
        await self.db.refresh(case)

        if changed:
            await _write_timeline_event(
                self.db,
                case_id=case.id,
                user_id=actor_id,
                event_type="case.updated",
                title="Case updated",
                description=f"Updated fields: {', '.join(changed)}",
            )

        await _write_audit_log(
            self.db,
            action="case.updated",
            user_id=actor_id,
            entity_type="case",
            entity_id=case.id,
            description=f"Updated case {case.id}: {', '.join(changed)}",
            ip_address=ip_address,
        )
        return case

    async def transition_status(
        self,
        case_id: uuid.UUID,
        new_status: str,
        actor_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Case:
        """Transition case status through the state machine."""
        case = await self.get_by_id(case_id)
        old_status = case.status

        # Validate transition
        validate_transition(old_status, new_status)

        case.status = new_status

        # Handle closed_at
        if new_status == "closed":
            case.closed_at = datetime.now(UTC)
        elif old_status == "closed" and new_status != "closed":
            case.closed_at = None  # Reopen clears closed_at

        await self.db.flush()
        await self.db.refresh(case)

        # Determine event type
        if old_status == "closed":
            event_type = "case.reopened"
            title = "Case reopened"
        elif new_status == "closed":
            event_type = "case.closed"
            title = "Case closed"
        else:
            event_type = "case.status_changed"
            title = f"Status changed: {old_status} → {new_status}"

        await _write_timeline_event(
            self.db,
            case_id=case.id,
            user_id=actor_id,
            event_type=event_type,
            title=title,
            old_value=old_status,
            new_value=new_status,
        )

        await _write_audit_log(
            self.db,
            action=f"case.status_changed.{new_status}",
            user_id=actor_id,
            entity_type="case",
            entity_id=case.id,
            description=f"Case status: {old_status} -> {new_status}",
            ip_address=ip_address,
        )
        return case

    async def get_timeline(self, case_id: uuid.UUID) -> list[TimelineEvent]:
        """Get all timeline events for a case, ordered chronologically."""
        result = await self.db.execute(
            select(TimelineEvent)
            .where(TimelineEvent.case_id == case_id)
            .order_by(TimelineEvent.created_at.asc())
        )
        return list(result.scalars().all())
