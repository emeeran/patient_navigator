"""Pydantic schemas for Document endpoints — DATA-005, API-030..037."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

# ── Enums ──────────────────────────────────────────────
FILE_TYPE_VALUES = ("pdf", "jpg", "jpeg", "png", "docx")
OCR_STATUS_VALUES = ("pending", "processing", "completed", "failed")

ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "image/jpeg": "jpg",
    "image/png": "png",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}


# ── Response schemas ─────────────────────────────────────


class DocumentResponse(BaseModel):
    """Full document metadata (excludes ocr_text)."""

    id: UUID
    case_id: UUID
    original_filename: str
    stored_filename: str
    file_type: str
    file_size_bytes: int
    mime_type: str
    ocr_status: str
    ocr_processed_at: datetime | None
    uploaded_by: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class DocumentListItem(BaseModel):
    """Subset for list views."""

    id: UUID
    case_id: UUID
    original_filename: str
    file_type: str
    file_size_bytes: str
    mime_type: str
    ocr_status: str
    uploaded_by: UUID
    created_at: datetime


class DocumentListResponse(BaseModel):
    """Paginated document list."""

    items: list[DocumentListItem]
    total: int
    page: int
    per_page: int


class OCRResultResponse(BaseModel):
    """OCR result with extracted text."""

    id: UUID
    ocr_status: str
    ocr_text: str | None
    ocr_processed_at: datetime | None


# ── ORM → dict helpers ────────────────────────────────────


def document_to_dict(doc: object) -> dict:
    """Convert a Document ORM object to a dict for DocumentResponse serialization."""
    return {
        "id": doc.id,
        "case_id": doc.case_id,
        "original_filename": doc.original_filename,
        "stored_filename": doc.stored_filename,
        "file_type": doc.file_type,
        "file_size_bytes": doc.file_size_bytes,
        "mime_type": doc.mime_type,
        "ocr_status": doc.ocr_status,
        "ocr_processed_at": doc.ocr_processed_at,
        "uploaded_by": doc.uploaded_by,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
        "deleted_at": doc.deleted_at,
    }


def document_list_item_to_dict(doc: object) -> dict:
    """Convert a Document ORM object to a dict for DocumentListItem serialization."""
    return {
        "id": doc.id,
        "case_id": doc.case_id,
        "original_filename": doc.original_filename,
        "file_type": doc.file_type,
        "file_size_bytes": doc.file_size_bytes,
        "mime_type": doc.mime_type,
        "ocr_status": doc.ocr_status,
        "uploaded_by": doc.uploaded_by,
        "created_at": doc.created_at,
    }
