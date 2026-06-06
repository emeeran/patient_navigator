"""Document management service — FEAT-004 upload, list, download, delete."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    FileTooLargeError,
    InvalidFileTypeError,
    NotFoundError,
)
from app.models.case import Case
from app.models.document import Document
from app.schemas.document import ALLOWED_MIME_TYPES

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


class DocumentService:
    """Handles document CRUD and file storage operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload(
        self,
        case_id: uuid.UUID,
        original_filename: str,
        mime_type: str,
        file_bytes: bytes,
        uploaded_by: uuid.UUID,
    ) -> Document:
        """Upload a new document for a case."""
        # Validate case exists
        case = await self.db.get(Case, case_id)
        if not case:
            raise NotFoundError("Case not found")

        # Validate MIME type
        if mime_type not in ALLOWED_MIME_TYPES:
            raise InvalidFileTypeError(f"File type {mime_type} not supported")

        # Validate file size
        if len(file_bytes) > MAX_FILE_SIZE:
            raise FileTooLargeError()

        file_type = ALLOWED_MIME_TYPES[mime_type]

        # Generate safe stored filename
        from app.core.file_storage import generate_stored_filename, save_file

        stored_filename = generate_stored_filename(file_type)
        save_file(file_bytes, stored_filename)

        document = Document(
            case_id=case_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_type=file_type,
            file_size_bytes=len(file_bytes),
            mime_type=mime_type,
            ocr_status="pending",
            uploaded_by=uploaded_by,
        )
        self.db.add(document)
        await self.db.flush()
        return document

    async def get_by_id(self, document_id: uuid.UUID) -> Document:
        """Get a document by ID."""
        result = await self.db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.deleted_at.is_(None),
            )
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise NotFoundError("Document not found")
        return doc

    async def list_for_case(
        self, case_id: uuid.UUID, page: int = 1, per_page: int = 20
    ) -> tuple[list[Document], int]:
        """List documents for a case with pagination."""
        base_query = select(Document).where(
            Document.case_id == case_id,
            Document.deleted_at.is_(None),
        )

        count_q = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        query = (
            base_query.order_by(Document.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def delete(self, document_id: uuid.UUID) -> None:
        """Soft delete a document."""
        doc = await self.get_by_id(document_id)
        doc.deleted_at = datetime.now(UTC)
        await self.db.flush()

    async def trigger_ocr(self, document_id: uuid.UUID) -> Document:
        """Trigger OCR processing for a document."""
        doc = await self.get_by_id(document_id)
        if doc.ocr_status == "processing":
            return doc  # Already processing

        doc.ocr_status = "processing"
        await self.db.flush()

        try:
            from app.services.ocr_service import extract_text_from_file

            text = extract_text_from_file(doc.stored_filename, doc.mime_type)
            if text:
                doc.ocr_text = text
                doc.ocr_status = "completed"
                doc.ocr_processed_at = datetime.now(UTC)
            else:
                # OCR engine unavailable or returned no text
                doc.ocr_status = "failed"
                doc.ocr_text = None
        except Exception:
            doc.ocr_status = "failed"

        await self.db.flush()
        return doc
