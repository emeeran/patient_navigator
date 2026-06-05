"""Follow-Up model — DATA-008."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class FollowUp(Base, TimestampMixin):
    __tablename__ = "follow_ups"

    case_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scheduled_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    follow_up_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # appointment, checkup, lab_test, imaging, referral
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="scheduled"
    )  # scheduled, completed, overdue, cancelled
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reminder_sent: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    created_by: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    def __repr__(self) -> str:
        return f"<FollowUp {self.id} type={self.follow_up_type} status={self.status}>"
