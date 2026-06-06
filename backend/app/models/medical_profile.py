"""MedicalProfile model — comprehensive patient health data for AI insights."""

from datetime import date
from typing import TYPE_CHECKING, Any

from sqlalchemy import Date, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.patient import Patient


class MedicalProfile(TimestampMixin, Base):
    """1:1 medical profile for a patient. Feeds AI insight generation."""

    __tablename__ = "medical_profiles"

    patient_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    blood_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    past_medical_history: Mapped[list[str] | None] = mapped_column(
        JSONB, nullable=True
    )
    family_medical_history: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB, nullable=True
    )
    chronic_conditions: Mapped[list[str] | None] = mapped_column(
        JSONB, nullable=True
    )
    current_medications: Mapped[list[str] | None] = mapped_column(
        JSONB, nullable=True
    )
    allergies: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships — no eager loading on back-ref to avoid recursive selectin cycle
    patient: Mapped["Patient"] = relationship(
        back_populates="medical_profile", lazy="noload"
    )

    __table_args__ = (
        Index("idx_medical_profiles_patient", "patient_id"),
    )

    def __repr__(self) -> str:
        return f"<MedicalProfile patient_id={self.patient_id}>"
