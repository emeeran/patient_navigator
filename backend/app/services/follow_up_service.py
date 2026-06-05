"""Follow-Up tracking service — FEAT-008."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    CompletedFollowUpError,
    InvalidStateTransitionError,
    NotFoundError,
    ValidationError,
)
from app.models.case import Case
from app.models.follow_up import FollowUp
from app.schemas.follow_up import FOLLOW_UP_STATUSES, FOLLOW_UP_TYPES


class FollowUpService:
    """Handles follow-up CRUD and status management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        case_id: uuid.UUID,
        data,
        created_by: uuid.UUID,
    ) -> FollowUp:
        """Schedule a new follow-up."""
        # Validate case exists
        case = await self.db.get(Case, case_id)
        if not case:
            raise NotFoundError("Case not found")

        if data.follow_up_type not in FOLLOW_UP_TYPES:
            raise ValidationError(f"Invalid follow-up type: {data.follow_up_type}")

        follow_up = FollowUp(
            case_id=case_id,
            scheduled_date=data.scheduled_date,
            follow_up_type=data.follow_up_type,
            notes=data.notes,
            status="scheduled",
            created_by=created_by,
        )
        self.db.add(follow_up)
        await self.db.flush()
        await self.db.refresh(follow_up)
        return follow_up

    async def get_by_id(self, follow_up_id: uuid.UUID) -> FollowUp:
        """Get a follow-up by ID."""
        result = await self.db.execute(
            select(FollowUp).where(FollowUp.id == follow_up_id)
        )
        fu = result.scalar_one_or_none()
        if not fu:
            raise NotFoundError("Follow-up not found")
        return fu

    async def list_for_case(
        self,
        case_id: uuid.UUID,
        page: int = 1,
        per_page: int = 20,
        status: str | None = None,
    ) -> tuple[list[FollowUp], int]:
        """List follow-ups for a case with pagination."""
        base_query = select(FollowUp).where(FollowUp.case_id == case_id)

        if status:
            base_query = base_query.where(FollowUp.status == status)

        count_q = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        query = (
            base_query.order_by(FollowUp.scheduled_date.asc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def list_upcoming(
        self,
        page: int = 1,
        per_page: int = 20,
        follow_up_type: str | None = None,
    ) -> tuple[list[FollowUp], int]:
        """List all upcoming (scheduled) follow-ups across cases."""
        now = datetime.now(UTC)
        base_query = select(FollowUp).where(
            FollowUp.status == "scheduled",
            FollowUp.scheduled_date >= now,
        )

        if follow_up_type:
            base_query = base_query.where(FollowUp.follow_up_type == follow_up_type)

        count_q = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        query = (
            base_query.order_by(FollowUp.scheduled_date.asc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def update(
        self,
        follow_up_id: uuid.UUID,
        data,
    ) -> FollowUp:
        """Update a follow-up."""
        fu = await self.get_by_id(follow_up_id)

        if fu.status == "completed":
            raise CompletedFollowUpError("Completed follow-ups cannot be modified")

        if data.scheduled_date is not None:
            fu.scheduled_date = data.scheduled_date
        if data.follow_up_type is not None:
            if data.follow_up_type not in FOLLOW_UP_TYPES:
                raise ValidationError(f"Invalid follow-up type: {data.follow_up_type}")
            fu.follow_up_type = data.follow_up_type
        if data.notes is not None:
            fu.notes = data.notes
        if data.status is not None:
            if data.status not in FOLLOW_UP_STATUSES:
                raise InvalidStateTransitionError(f"Invalid status: {data.status}")
            fu.status = data.status
            if data.status == "completed":
                fu.completed_at = datetime.now(UTC)

        await self.db.flush()
        await self.db.refresh(fu)
        return fu

    async def complete(
        self,
        follow_up_id: uuid.UUID,
        completed_by: uuid.UUID,
    ) -> FollowUp:
        """Mark a follow-up as completed."""
        fu = await self.get_by_id(follow_up_id)
        fu.status = "completed"
        fu.completed_at = datetime.now(UTC)
        fu.completed_by = completed_by
        await self.db.flush()
        await self.db.refresh(fu)
        return fu

    async def mark_overdue(self) -> int:
        """Mark all past-due scheduled follow-ups as overdue. Returns count updated."""
        now = datetime.now(UTC)
        result = await self.db.execute(
            select(FollowUp).where(
                FollowUp.status == "scheduled",
                FollowUp.scheduled_date < now,
            )
        )
        overdue = result.scalars().all()
        for fu in overdue:
            fu.status = "overdue"
        await self.db.flush()
        return len(overdue)
