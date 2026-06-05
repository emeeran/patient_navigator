"""Document model — DATA-005."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class Document(TimestampMixin, Base):
    __tablename__ = "documents"

    case_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    ocr_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    uploaded_by: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("idx_documents_case", "case_id"),
        Index("idx_documents_uploaded_by", "uploaded_by"),
        Index("idx_documents_ocr_status", "ocr_status"),
    )

    def __repr__(self) -> str:
        return f"<Document {self.id} {self.original_filename}>"
