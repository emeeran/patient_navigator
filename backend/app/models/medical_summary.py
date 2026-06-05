"""Clinician Review model — DATA-011."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class ClinicianReview(Base, TimestampMixin):
    __tablename__ = "clinician_reviews"

    case_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    ai_disclaimer_acknowledged: Mapped[bool] = mapped_column(
        default=False, nullable=False, server_default="false"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="draft"
    )  # draft, approved, rejected
    reviewer_comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<ClinicianReview {self.id} case={self.case_id} status={self.status}>"
