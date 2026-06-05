"""File storage utilities — local filesystem with UUID-based filenames."""

import uuid
from pathlib import Path

from app.core.config import settings


def _ensure_upload_dir() -> Path:
    """Create upload directory if it doesn't exist."""
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def generate_stored_filename(extension: str) -> str:
    """Generate a UUID-based filename with the given extension.

    The extension is sanitized to prevent path traversal.
    """
    safe_ext = extension.lower().strip(".")
    return f"{uuid.uuid4()}.{safe_ext}"


def save_file(file_bytes: bytes, stored_filename: str) -> Path:
    """Save file bytes to the upload directory.

    Returns the absolute path to the saved file.
    The stored_filename must be a UUID-based name (no path components).
    """
    upload_dir = _ensure_upload_dir()
    # Prevent path traversal — reject any filename with path separators
    if "/" in stored_filename or "\\" in stored_filename or ".." in stored_filename:
        raise ValueError(f"Invalid stored filename: {stored_filename}")
    file_path = upload_dir / stored_filename
    file_path.write_bytes(file_bytes)
    return file_path


def read_file(stored_filename: str) -> bytes:
    """Read file bytes from the upload directory.

    Raises FileNotFoundError if the file doesn't exist.
    """
    upload_dir = _ensure_upload_dir()
    if "/" in stored_filename or "\\" in stored_filename or ".." in stored_filename:
        raise ValueError(f"Invalid stored filename: {stored_filename}")
    file_path = upload_dir / stored_filename
    return file_path.read_bytes()


def file_exists(stored_filename: str) -> bool:
    """Check if a file exists in the upload directory."""
    upload_dir = _ensure_upload_dir()
    if "/" in stored_filename or "\\" in stored_filename or ".." in stored_filename:
        return False
    return (upload_dir / stored_filename).exists()


def delete_file(stored_filename: str) -> bool:
    """Delete a file from the upload directory.

    Returns True if the file was deleted, False if it didn't exist.
    """
    upload_dir = _ensure_upload_dir()
    if "/" in stored_filename or "\\" in stored_filename or ".." in stored_filename:
        return False
    file_path = upload_dir / stored_filename
    if file_path.exists():
        file_path.unlink()
        return True
    return False
