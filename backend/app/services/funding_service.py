"""Funding program service — FEAT-007 CRUD and search."""

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.funding_program import FundingProgram
from app.schemas.funding_program import FundingProgramUpdateRequest


class FundingService:
    """Handles funding program CRUD, search, and soft-archive operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> FundingProgram:
        """Create a new funding program."""
        program = FundingProgram(**data)
        self.db.add(program)
        await self.db.flush()
        return program

    async def get_by_id(self, program_id: uuid.UUID) -> FundingProgram:
        """Get a funding program by ID. Raises NotFoundError if not found or not active."""
        result = await self.db.execute(
            select(FundingProgram).where(FundingProgram.id == program_id)
        )
        program = result.scalar_one_or_none()
        if not program or not program.is_active:
            raise NotFoundError("Funding program not found")
        return program

    async def get_by_id_any(self, program_id: uuid.UUID) -> FundingProgram:
        """Get a funding program by ID regardless of active status."""
        result = await self.db.execute(
            select(FundingProgram).where(FundingProgram.id == program_id)
        )
        program = result.scalar_one_or_none()
        if not program:
            raise NotFoundError("Funding program not found")
        return program

    async def list_programs(
        self,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
        sort: str | None = None,
    ) -> tuple[list[FundingProgram], int]:
        """List funding programs with optional filtering, search, and pagination."""
        base_query = select(FundingProgram)

        # Filter by active status
        if is_active is not None:
            base_query = base_query.where(FundingProgram.is_active == is_active)

        # Search by name or description
        if search:
            search_term = f"%{search}%"
            base_query = base_query.where(
                or_(
                    FundingProgram.name.ilike(search_term),
                    FundingProgram.description.ilike(search_term),
                    FundingProgram.provider.ilike(search_term),
                )
            )

        # Count total
        count_q = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        # Sort
        sort_column = FundingProgram.created_at
        sort_desc = True
        if sort:
            desc = sort.startswith("-")
            col_name = sort.lstrip("-")
            column_map = {
                "name": FundingProgram.name,
                "max_amount": FundingProgram.max_amount,
                "min_amount": FundingProgram.min_amount,
                "deadline": FundingProgram.deadline,
                "created_at": FundingProgram.created_at,
            }
            if col_name in column_map:
                sort_column = column_map[col_name]
                sort_desc = desc

        if sort_desc:
            query = base_query.order_by(sort_column.desc())
        else:
            query = base_query.order_by(sort_column.asc())

        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def update(
        self, program_id: uuid.UUID, data: FundingProgramUpdateRequest
    ) -> FundingProgram:
        """Update a funding program. Only provided fields are updated."""
        program = await self.get_by_id_any(program_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(program, field, value)
        await self.db.flush()
        await self.db.refresh(program)
        return program

    async def archive(self, program_id: uuid.UUID) -> None:
        """Soft-archive a funding program by setting is_active=False."""
        program = await self.get_by_id_any(program_id)
        program.is_active = False
        await self.db.flush()
