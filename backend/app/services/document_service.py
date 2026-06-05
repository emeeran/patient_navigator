"""Document management service — FEAT-004 upload, list, download, delete."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidFileTypeError, NotFoundError
from app.models.document import Document
from app.schemas.document import DocumentCreateRequest


class DocumentService:
    """Handles document CRUD and file storage operations."""

    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/tiff",
        "image/bmp",
        "text/plain",
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        case_id: uuid.UUID,
        data: DocumentCreateRequest,
        file_content: bytes,
        actor_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Document:
        """Upload a new document for a case."""
        if data.mime_type not in self.ALLOWED_MIME_TYPES:
            raise InvalidFileTypeError(f"File type {data.mime_type} not supported")

        document = Document(
            case_id=case_id,
            file_name=data.file_name,
            mime_type=data.mime_type,
            file_size=len(file_content),
            storage_path="",  # Will be set after storage
            uploaded_by=actor_id,
        )
        self.db.add(document)
        await self.db.flush()

        # Store file (filesystem in V1, S3 in V2)
        from app.core.file_storage import save_file

        storage_path = await save_file(document.id, file_content)
        document.storage_path = storage_path
        await self.db.flush()

        return document

    async def get_by_id(self, document_id: uuid.UUID) -> Document:
        """Get a document by ID."""
        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise NotFoundError("Document not found")
        return doc

    async def list_for_case(
        self, case_id: uuid.UUID, page: int = 1, per_page: int = 20
    ) -> tuple[list[Document], int]:
        """List documents for a case with pagination."""
        from sqlalchemy import func

        count_q = select(func.count()).select_from(Document).where(Document.case_id == case_id)
        total = (await self.db.execute(count_q)).scalar() or 0

        query = (
            select(Document)
            .where(Document.case_id == case_id)
            .order_by(Document.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def delete(self, document_id: uuid.UUID, actor_id: uuid.UUID) -> None:
        """Soft delete a document."""
        doc = await self.get_by_id(document_id)
        doc.deleted_at = datetime.now(UTC)
        await self.db.flush()

    async def get_file_content(self, document_id: uuid.UUID) -> tuple[Document, bytes]:
        """Get document metadata and file content for download."""
        doc = await self.get_by_id(document_id)
        from app.core.file_storage import load_file

        content = await load_file(doc.storage_path)
        return doc, content
