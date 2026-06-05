"""FundingProgram model — DATA-007."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class FundingProgram(TimestampMixin, Base):
    __tablename__ = "funding_programs"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str | None] = mapped_column(String(255), nullable=True)
    program_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    eligibility_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    application_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", default=True
    )
    contact_email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    __table_args__ = (
        Index("idx_funding_programs_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<FundingProgram {self.id} {self.name}>"
