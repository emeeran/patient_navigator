"""Document endpoints — FEAT-004, API-030..037."""

import uuid

from fastapi import APIRouter, Depends, Query, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_role
from app.core.database import get_db
from app.models.user import User
from app.schemas.document import (
    DocumentListItem,
    DocumentListResponse,
    OCRResultResponse,
    document_list_item_to_dict,
    document_to_dict,
)
from app.services.document_service import DocumentService

router = APIRouter()


@router.post("/cases/{case_id}/documents/upload", status_code=201)
async def upload_document(
    case_id: uuid.UUID,
    file: UploadFile,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "navigator")),
):
    """API-030: Upload a document to a case."""
    file_bytes = await file.read()
    service = DocumentService(db)
    doc = await service.upload(
        case_id=case_id,
        original_filename=file.filename or "unnamed",
        mime_type=file.content_type or "application/octet-stream",
        file_bytes=file_bytes,
        uploaded_by=current_user.id,
    )
    return document_to_dict(doc)


@router.get("/cases/{case_id}/documents")
async def list_case_documents(
    case_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """API-031: List documents for a case."""
    service = DocumentService(db)
    items, total = await service.list_for_case(case_id, page, per_page)
    return DocumentListResponse(
        items=[DocumentListItem(**document_list_item_to_dict(d)) for d in items],
        total=total,
        page=page,
        per_page=per_page,
    ).model_dump()


@router.get("/documents/{document_id}")
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """API-032: Get document metadata."""
    service = DocumentService(db)
    doc = await service.get_by_id(document_id)
    return document_to_dict(doc)


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "navigator", "clinician"),
    ),
):
    """API-033: Download document file."""
    service = DocumentService(db)
    doc = await service.get_by_id(document_id)

    from app.core.file_storage import read_file

    file_bytes = read_file(doc.stored_filename)

    return Response(
        content=file_bytes,
        media_type=doc.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{doc.original_filename}"',
            "Content-Length": str(len(file_bytes)),
        },
    )


@router.get("/documents/{document_id}/preview")
async def preview_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """API-034: Preview document (metadata + OCR text if available)."""
    service = DocumentService(db)
    doc = await service.get_by_id(document_id)
    data = document_to_dict(doc)
    data["ocr_text"] = doc.ocr_text
    return data


@router.post("/documents/{document_id}/ocr")
async def trigger_ocr(
    document_id: uuid.UUID,
    language: str | None = Query(None, description="OCR language: 'tamil', 'english', or omit for both"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "navigator")),
):
    """API-035: Trigger OCR processing for a document."""
    service = DocumentService(db)
    doc = await service.trigger_ocr(document_id, language=language)
    return OCRResultResponse(
        id=doc.id,
        ocr_status=doc.ocr_status,
        ocr_text=doc.ocr_text,
        ocr_processed_at=doc.ocr_processed_at,
    ).model_dump()


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "navigator")),
):
    """API-036: Delete a document (soft delete)."""
    service = DocumentService(db)
    await service.delete(document_id)
    return None
