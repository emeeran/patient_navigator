"""Hospital directory service — FEAT-006."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.hospital import Hospital


class HospitalService:
    """Handles hospital CRUD and search."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data) -> Hospital:
        """Create a new hospital."""
        hospital = Hospital(
            name=data.name,
            city=data.city,
            state=data.state,
            address=data.address,
            phone=data.phone,
            email=data.email,
            website=data.website,
            specialties=data.specialties,
            has_financial_assistance=data.has_financial_assistance,
            rating=data.rating,
            latitude=data.latitude,
            longitude=data.longitude,
            is_active=True,
        )
        self.db.add(hospital)
        await self.db.flush()
        await self.db.refresh(hospital)
        return hospital

    async def get_by_id(self, hospital_id: uuid.UUID) -> Hospital:
        """Get an active hospital by ID."""
        result = await self.db.execute(
            select(Hospital).where(
                Hospital.id == hospital_id, Hospital.is_active.is_(True)
            )
        )
        hospital = result.scalar_one_or_none()
        if not hospital:
            raise NotFoundError("Hospital not found")
        return hospital

    async def list_hospitals(
        self,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        city: str | None = None,
        specialty: str | None = None,
        has_financial_assistance: bool | None = None,
        is_active: bool | None = True,
        sort: str | None = None,
    ) -> tuple[list[Hospital], int]:
        """List hospitals with filters and pagination."""
        base_query = select(Hospital)

        if is_active is not None:
            base_query = base_query.where(Hospital.is_active == is_active)

        if search:
            base_query = base_query.where(Hospital.name.ilike(f"%{search}%"))

        if city:
            base_query = base_query.where(Hospital.city.ilike(f"%{city}%"))

        if specialty:
            base_query = base_query.where(
                Hospital.specialties.ilike(f"%{specialty}%")
            )

        if has_financial_assistance is not None:
            base_query = base_query.where(
                Hospital.has_financial_assistance == has_financial_assistance
            )

        count_q = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        # Sorting
        if sort == "-rating":
            base_query = base_query.order_by(Hospital.rating.desc().nulls_last())
        elif sort == "rating":
            base_query = base_query.order_by(Hospital.rating.asc().nulls_last())
        elif sort == "name":
            base_query = base_query.order_by(Hospital.name.asc())
        else:
            base_query = base_query.order_by(Hospital.created_at.desc())

        query = base_query.offset((page - 1) * per_page).limit(per_page)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def update(self, hospital_id: uuid.UUID, data) -> Hospital:
        """Update a hospital."""
        hospital = await self.get_by_id(hospital_id)

        for field in (
            "name", "city", "state", "address", "phone", "email", "website",
            "specialties", "has_financial_assistance", "rating", "is_active",
            "latitude", "longitude",
        ):
            value = getattr(data, field, None)
            if value is not None:
                setattr(hospital, field, value)

        await self.db.flush()
        await self.db.refresh(hospital)
        return hospital

    async def archive(self, hospital_id: uuid.UUID) -> None:
        """Soft-delete a hospital."""
        hospital = await self.get_by_id(hospital_id)
        hospital.is_active = False
        await self.db.flush()
