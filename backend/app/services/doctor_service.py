"""Doctor directory service."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.doctor import Doctor


class DoctorService:
    """Handles doctor CRUD and search."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data) -> Doctor:
        """Create a new doctor."""
        doctor = Doctor(
            name=data.name,
            city=data.city,
            state=data.state,
            address=data.address,
            phone=data.phone,
            email=data.email,
            website=data.website,
            specialty=data.specialty,
            qualification=data.qualification,
            registration_number=data.registration_number,
            medical_council=data.medical_council,
            hospital_name=data.hospital_name,
            practice_type=data.practice_type,
            latitude=data.latitude,
            longitude=data.longitude,
            is_active=True,
        )
        self.db.add(doctor)
        await self.db.flush()
        await self.db.refresh(doctor)
        return doctor

    async def get_by_id(self, doctor_id: uuid.UUID) -> Doctor:
        """Get an active doctor by ID."""
        result = await self.db.execute(
            select(Doctor).where(
                Doctor.id == doctor_id, Doctor.is_active.is_(True)
            )
        )
        doctor = result.scalar_one_or_none()
        if not doctor:
            raise NotFoundError("Doctor not found")
        return doctor

    async def list_doctors(
        self,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        city: str | None = None,
        specialty: str | None = None,
        practice_type: str | None = None,
        is_active: bool | None = True,
        sort: str | None = None,
    ) -> tuple[list[Doctor], int]:
        """List doctors with filters and pagination."""
        base_query = select(Doctor)

        if is_active is not None:
            base_query = base_query.where(Doctor.is_active == is_active)

        if search:
            base_query = base_query.where(Doctor.name.ilike(f"%{search}%"))

        if city:
            base_query = base_query.where(Doctor.city.ilike(f"%{city}%"))

        if specialty:
            base_query = base_query.where(Doctor.specialty.ilike(f"%{specialty}%"))

        if practice_type:
            base_query = base_query.where(Doctor.practice_type == practice_type)

        count_q = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        # Sorting
        if sort == "name":
            base_query = base_query.order_by(Doctor.name.asc())
        elif sort == "-name":
            base_query = base_query.order_by(Doctor.name.desc())
        elif sort == "city":
            base_query = base_query.order_by(Doctor.city.asc())
        else:
            base_query = base_query.order_by(Doctor.created_at.desc())

        query = base_query.offset((page - 1) * per_page).limit(per_page)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def update(self, doctor_id: uuid.UUID, data) -> Doctor:
        """Update a doctor."""
        doctor = await self.get_by_id(doctor_id)

        for field in (
            "name", "city", "state", "address", "phone", "email", "website",
            "specialty", "qualification", "registration_number", "medical_council",
            "hospital_name", "practice_type", "is_active", "latitude", "longitude",
        ):
            value = getattr(data, field, None)
            if value is not None:
                setattr(doctor, field, value)

        await self.db.flush()
        await self.db.refresh(doctor)
        return doctor

    async def archive(self, doctor_id: uuid.UUID) -> None:
        """Soft-delete a doctor."""
        doctor = await self.get_by_id(doctor_id)
        doctor.is_active = False
        await self.db.flush()
