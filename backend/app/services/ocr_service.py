"""OCR service — uses Tesseract (primary) or PaddleOCR for text extraction.

Supports English and Tamil OCR. Tamil is used when:
- The `language` parameter is set to "tamil" or "tam"
- Both English + Tamil are used by default for best coverage
"""

import logging
import subprocess
import tempfile
from pathlib import Path

from app.core.file_storage import file_exists

logger = logging.getLogger(__name__)

_ocr_engine: object | None = None
_ocr_engine_lang: str | None = None

# Languages we support
SUPPORTED_LANGS = {"english", "eng", "tamil", "tam"}


def _tesseract_langs(language: str | None = None) -> str:
    """Return the tesseract `-l` argument for the given language.

    Default: eng+tam (both English and Tamil for maximum coverage).
    """
    if language and language.lower() in ("tamil", "tam"):
        return "tam+eng"
    if language and language.lower() in ("english", "eng"):
        return "eng"
    # Default: both languages for best results on mixed-language docs
    return "eng+tam" if _tesseract_has_lang("tam") else "eng"


def _tesseract_has_lang(lang: str) -> bool:
    """Check if Tesseract has a specific language pack installed."""
    try:
        result = subprocess.run(
            ["tesseract", "--list-langs"],
            capture_output=True, text=True, timeout=5,
        )
        return lang in result.stdout.split()
    except Exception:
        return False


def _get_ocr_engine(language: str | None = None):
    """Lazy-load PaddleOCR engine (expensive to initialize).

    Returns None if PaddleOCR is not installed or fails to initialize.
    Reinitializes if the language changes.
    """
    global _ocr_engine, _ocr_engine_lang

    paddle_lang = "ta" if language and language.lower() in ("tamil", "tam") else "en"

    if _ocr_engine is not None and _ocr_engine_lang == paddle_lang:
        return _ocr_engine

    try:
        from paddleocr import PaddleOCR

        _ocr_engine = PaddleOCR(lang=paddle_lang)
        _ocr_engine_lang = paddle_lang
        logger.info("PaddleOCR engine initialized (lang=%s)", paddle_lang)
    except ImportError:
        logger.info("PaddleOCR not installed — using Tesseract fallback")
    except Exception as exc:
        logger.warning("PaddleOCR init failed: %s — using Tesseract fallback", exc)
    return _ocr_engine


def _tesseract_available() -> bool:
    """Check if the tesseract CLI is installed."""
    try:
        result = subprocess.run(["tesseract", "--version"], capture_output=True, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def extract_text_from_file(
    stored_filename: str,
    mime_type: str,
    language: str | None = None,
) -> str:
    """Extract text from a stored document file.

    Args:
        stored_filename: Path to the stored file.
        mime_type: MIME type of the file.
        language: OCR language — "english"/"eng", "tamil"/"tam", or None (auto-detect both).

    Returns extracted text string, or empty string if OCR is unavailable.
    Raises RuntimeError on processing failure.
    """
    if not file_exists(stored_filename):
        raise FileNotFoundError(f"File not found: {stored_filename}")

    if mime_type == "application/pdf":
        return _extract_pdf(stored_filename, language)
    elif mime_type.startswith("image/"):
        return _extract_image(stored_filename, language)
    elif "wordprocessingml" in mime_type:
        from app.core.file_storage import read_file
        return _extract_from_docx(read_file(stored_filename))
    else:
        return ""


def _extract_image(stored_filename: str, language: str | None = None) -> str:
    """Extract text from an image using Tesseract (fast) or PaddleOCR."""
    from app.core.file_storage import _ensure_upload_dir

    file_path = (_ensure_upload_dir() / stored_filename).resolve()

    # Try Tesseract first (fast, reliable)
    if _tesseract_available():
        return _tesseract_ocr(str(file_path), language)

    # Fall back to PaddleOCR
    engine = _get_ocr_engine(language)
    if engine is not None:
        result = engine.ocr(str(file_path))
        return _join_paddle_result(result)

    return ""


def _extract_pdf(stored_filename: str, language: str | None = None) -> str:
    """Extract text from a PDF."""
    from app.core.file_storage import _ensure_upload_dir, read_file

    file_path = (_ensure_upload_dir() / stored_filename).resolve()

    # Tesseract can handle PDFs directly
    if _tesseract_available():
        return _tesseract_ocr(str(file_path), language)

    # Try PaddleOCR with temp file
    engine = _get_ocr_engine(language)
    if engine is not None:
        file_bytes = read_file(stored_filename)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        try:
            result = engine.ocr(tmp_path)
            return _join_paddle_result(result)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    return ""


def _tesseract_ocr(file_path: str, language: str | None = None) -> str:
    """Run tesseract CLI on a file and return extracted text."""
    langs = _tesseract_langs(language)
    try:
        result = subprocess.run(
            ["tesseract", "-l", langs, file_path, "stdout"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            text = result.stdout.strip()
            return text
        logger.warning("Tesseract failed (rc=%d): %s", result.returncode, result.stderr[:200])
        return ""
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        logger.warning("Tesseract error: %s", exc)
        return ""


def _extract_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file using raw XML parsing."""
    try:
        import io
        import re
        import zipfile

        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            text_parts = []
            for name in zf.namelist():
                if name.startswith("word/document") and name.endswith(".xml"):
                    content = zf.read(name).decode("utf-8")
                    text = re.sub(r"<[^>]+>", " ", content)
                    text = re.sub(r"\s+", " ", text).strip()
                    if text:
                        text_parts.append(text)
            return "\n".join(text_parts)
    except Exception as e:
        logger.warning(f"DOCX text extraction failed: {e}")
        return ""


def _join_paddle_result(result) -> str:
    """Join PaddleOCR result blocks into a single text string."""
    if not result:
        return ""

    lines = []
    for page in result:
        if not page:
            continue
        if isinstance(page, dict):
            rec_text = page.get("rec_text")
            if rec_text:
                lines.append(rec_text)
        elif isinstance(page, list):
            for line in page:
                if isinstance(line, dict):
                    rec_text = line.get("rec_text")
                    if rec_text:
                        lines.append(rec_text)
                elif isinstance(line, (list, tuple)) and len(line) >= 2:
                    text = line[1][0] if isinstance(line[1], (list, tuple)) else str(line[1])
                    lines.append(text)

    return "\n".join(lines)
