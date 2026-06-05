"""Case model — DATA-004."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.user import User


class Case(TimestampMixin, Base):
    __tablename__ = "cases"

    patient_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    diagnosis: Mapped[str] = mapped_column(String(5000), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="new")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, server_default="medium")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_hospital_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), nullable=True  # FK deferred to Phase 5 when Hospital model is created
    )
    applied_funding_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), nullable=True  # FK deferred to Phase 5 when FundingProgram model is created
    )
    assigned_clinician_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    patient: Mapped["Patient"] = relationship(lazy="selectin")
    creator: Mapped["User"] = relationship(foreign_keys=[created_by], lazy="selectin")

    __table_args__ = (
        Index("idx_cases_patient", "patient_id"),
        Index("idx_cases_status", "status"),
        Index("idx_cases_priority", "priority"),
        Index("idx_cases_created_by", "created_by"),
        Index("idx_cases_status_priority", "status", "priority"),
    )

    def __repr__(self) -> str:
        return f"<Case {self.id} status={self.status}>"
