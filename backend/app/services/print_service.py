"""Orchestrates print-job submission: validates the target printer and the
upload, stages the file safely on disk, hands it to CupsService, then always
cleans up the temporary file regardless of outcome.
"""

from __future__ import annotations

from fastapi import UploadFile

from app.services.cups import CupsService, PrinterNotFoundError
from app.services.printer_service import map_printer_state
from app.utils.files import (
    cleanup_workspace,
    create_job_workspace,
    read_upload_limited,
    save_upload,
    validate_content,
    validate_extension,
)
from app.utils.security import is_valid_printer_name


class PrinterNotAcceptingJobsError(Exception):
    """Raised when the target printer exists but cannot take new jobs right now."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class PrintService:
    def __init__(self, cups_service: CupsService, max_upload_size_bytes: int):
        self._cups = cups_service
        self._max_upload_size_bytes = max_upload_size_bytes

    def _ensure_printer_ready(self, printer: str) -> dict:
        if not is_valid_printer_name(printer):
            raise PrinterNotFoundError(f"Printer '{printer}' not found")

        attrs = self._cups.get_printer_attributes(printer)  # raises PrinterNotFoundError

        if map_printer_state(attrs) == "STOPPED":
            raise PrinterNotAcceptingJobsError("PRINTER_STOPPED", f"Printer '{printer}' is currently stopped")
        if not attrs.get("printer-is-accepting-jobs", False):
            raise PrinterNotAcceptingJobsError(
                "PRINTER_UNAVAILABLE", f"Printer '{printer}' is not accepting jobs"
            )
        return attrs

    async def submit_print(
        self,
        printer: str,
        file: UploadFile,
        copies: int,
        page_ranges: str | None,
        media: str | None,
        orientation: str | None,
        color: str | None,
        duplex: str | None,
    ) -> dict:
        self._ensure_printer_ready(printer)

        extension = validate_extension(file.filename or "")
        content = await read_upload_limited(file, self._max_upload_size_bytes)
        validate_content(extension, content)

        workspace = create_job_workspace()
        try:
            file_path = save_upload(workspace, extension, content)

            options: dict[str, str] = {}
            if copies > 1:
                options["copies"] = str(copies)
            if page_ranges:
                options["page-ranges"] = page_ranges
            if media:
                options["media"] = media
            if orientation:
                options["orientation-requested"] = orientation
            if color:
                options["print-color-mode"] = color
            if duplex:
                options["sides"] = duplex

            # Never pass the raw user-supplied filename anywhere but the response body.
            title = (file.filename or "document").replace("/", "_").replace("\\", "_")[:255]

            job_id = self._cups.submit_print_job(
                printer=printer,
                file_path=str(file_path),
                title=title,
                options=options,
            )
        finally:
            cleanup_workspace(workspace)

        return {
            "success": True,
            "job_id": job_id,
            "printer": printer,
            "filename": title,
            "status": "queued",
        }
