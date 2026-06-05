"""OCR service — wraps PaddleOCR for text extraction from documents."""

import logging

from app.core.file_storage import file_exists

logger = logging.getLogger(__name__)

_ocr_engine = None


def _get_ocr_engine():
    """Lazy-load PaddleOCR engine (expensive to initialize)."""
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from paddleocr import PaddleOCR

            _ocr_engine = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
            logger.info("PaddleOCR engine initialized")
        except ImportError:
            logger.warning("PaddleOCR not installed — OCR will return empty text")
            return None
    return _ocr_engine


def extract_text_from_file(stored_filename: str, mime_type: str) -> str:
    """Extract text from a stored document file.

    Returns extracted text string, or empty string if OCR is unavailable.
    Raises RuntimeError on processing failure.
    """
    if not file_exists(stored_filename):
        raise FileNotFoundError(f"File not found: {stored_filename}")

    engine = _get_ocr_engine()
    if engine is None:
        # PaddleOCR not available — return empty text
        return ""

    try:
        from app.core.file_storage import read_file

        file_bytes = read_file(stored_filename)

        if mime_type == "application/pdf":
            return _extract_from_pdf(engine, file_bytes)
        elif mime_type.startswith("image/"):
            return _extract_from_image(engine, stored_filename)
        elif "wordprocessingml" in mime_type:
            return _extract_from_docx(file_bytes)
        else:
            return ""
    except Exception as e:
        logger.error(f"OCR failed for {stored_filename}: {e}")
        raise RuntimeError(f"OCR processing failed: {e}") from e


def _extract_from_image(engine, stored_filename: str) -> str:
    """Extract text from an image file using PaddleOCR."""
    from app.core.file_storage import _ensure_upload_dir

    file_path = _ensure_upload_dir() / stored_filename
    result = engine.ocr(str(file_path), cls=True)
    return _join_ocr_result(result)


def _extract_from_pdf(engine, file_bytes: bytes) -> str:
    """Extract text from a PDF file.

    For simplicity, converts first page to image and runs OCR.
    Full PDF OCR would require pdf2image (poppler) — deferred.
    """
    # Try direct OCR on the raw bytes (PaddleOCR handles some PDFs)
    import tempfile
    from pathlib import Path

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        result = engine.ocr(tmp_path, cls=True)
        return _join_ocr_result(result)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _extract_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file using python-docx or raw XML parsing."""
    try:
        import io
        import zipfile

        # Simple text extraction from DOCX (no extra dependency needed)
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            text_parts = []
            for name in zf.namelist():
                if name.startswith("word/document") and name.endswith(".xml"):
                    content = zf.read(name).decode("utf-8")
                    # Strip XML tags — crude but effective for plain text
                    import re

                    text = re.sub(r"<[^>]+>", " ", content)
                    text = re.sub(r"\s+", " ", text).strip()
                    if text:
                        text_parts.append(text)
            return "\n".join(text_parts)
    except Exception as e:
        logger.warning(f"DOCX text extraction failed: {e}")
        return ""


def _join_ocr_result(result) -> str:
    """Join PaddleOCR result blocks into a single text string."""
    if not result or not result[0]:
        return ""
    lines = []
    for line in result[0]:
        if line and len(line) >= 2:
            lines.append(line[1][0])  # text content
    return "\n".join(lines)
