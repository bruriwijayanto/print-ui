"""File upload validation and safe temporary-file handling for print jobs.

Uploaded files are never trusted: the user-supplied filename is never used
as a filesystem path, and the declared extension is always cross-checked
against the file's actual magic bytes before it touches CUPS.
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import filetype

JOBS_ROOT = Path("/tmp/cups-print-jobs")

# Extension -> mime types accepted for that extension, verified via magic bytes.
# ".txt" has no magic bytes; it is validated separately in validate_content().
_ALLOWED_EXTENSIONS: dict[str, set[str]] = {
    ".pdf": {"application/pdf"},
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".txt": set(),
}


class InvalidFileError(Exception):
    """Raised when the uploaded file's extension or content is invalid."""


class FileTooLargeError(Exception):
    """Raised when the uploaded file exceeds the configured size limit."""


def validate_extension(filename: str) -> str:
    """Returns the lowercased, allowed extension, or raises InvalidFileError."""
    suffix = Path(filename or "").suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(_ALLOWED_EXTENSIONS))
        raise InvalidFileError(f"File type '{suffix or 'unknown'}' is not supported. Allowed: {allowed}")
    return suffix


def validate_content(extension: str, content: bytes) -> None:
    """Cross-checks the file's real magic bytes against its declared extension."""
    if not content:
        raise InvalidFileError("Uploaded file is empty")

    guessed = filetype.guess(content)

    if extension == ".txt":
        if guessed is not None:
            raise InvalidFileError(f"File declared as .txt but its content looks like '{guessed.mime}'")
        if b"\x00" in content:
            raise InvalidFileError("File declared as .txt appears to be binary, not text")
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise InvalidFileError("File declared as .txt is not valid UTF-8 text") from exc
        return

    allowed_mimes = _ALLOWED_EXTENSIONS[extension]
    if guessed is None or guessed.mime not in allowed_mimes:
        actual = guessed.mime if guessed else "unknown"
        raise InvalidFileError(f"File content ('{actual}') does not match its extension ('{extension}')")


async def read_upload_limited(upload, max_bytes: int) -> bytes:
    """Reads an UploadFile in chunks, aborting as soon as max_bytes is exceeded
    so an oversized upload cannot be fully buffered into memory first."""
    chunks: list[bytes] = []
    total = 0
    chunk_size = 1024 * 1024
    while True:
        chunk = await upload.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise FileTooLargeError(f"File exceeds the maximum allowed size of {max_bytes // (1024 * 1024)} MB")
        chunks.append(chunk)
    return b"".join(chunks)


def create_job_workspace() -> Path:
    """Creates a fresh /tmp/cups-print-jobs/<uuid>/ directory and returns its path."""
    workspace = JOBS_ROOT / str(uuid.uuid4())
    workspace.mkdir(parents=True, exist_ok=False, mode=0o700)
    return workspace


def save_upload(workspace: Path, extension: str, content: bytes) -> Path:
    """Writes validated content under a fixed filename inside workspace — never
    the user-supplied filename — so no path is ever built from user input."""
    destination = workspace / f"document{extension}"
    destination.write_bytes(content)
    return destination


def cleanup_workspace(workspace: Path) -> None:
    shutil.rmtree(workspace, ignore_errors=True)
