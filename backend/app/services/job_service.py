"""Maps raw CUPS/IPP job attribute dicts to the shapes the API exposes.

Mirrors printer_service.py: all "what does this IPP attribute mean" logic
lives here so routes stay dumb and cups.py stays a thin CUPS/IPP wrapper.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.services.cups import CupsService
from app.services.printer_service import printer_name_from_uri

# IPP job-state values (RFC 8011).
_JOB_STATE_PENDING = 3
_JOB_STATE_PENDING_HELD = 4
_JOB_STATE_PROCESSING = 5
_JOB_STATE_PROCESSING_STOPPED = 6
_JOB_STATE_CANCELED = 7
_JOB_STATE_ABORTED = 8
_JOB_STATE_COMPLETED = 9

_JOB_STATE_MAP = {
    _JOB_STATE_PENDING: "PENDING",
    _JOB_STATE_PENDING_HELD: "PENDING",
    _JOB_STATE_PROCESSING: "PROCESSING",
    _JOB_STATE_PROCESSING_STOPPED: "PROCESSING",
    _JOB_STATE_CANCELED: "CANCELED",
    _JOB_STATE_ABORTED: "FAILED",
    _JOB_STATE_COMPLETED: "COMPLETED",
}

_TERMINAL_STATES = {"COMPLETED", "CANCELED", "FAILED"}

# Job attribute names that mirror the print options accepted by POST /api/print.
_OPTION_ATTRS = ("copies", "page-ranges", "media", "orientation-requested", "print-color-mode", "sides")


class JobNotCancelableError(Exception):
    """Raised when attempting to cancel a job that already reached a terminal state."""


def map_job_state(attrs: dict) -> str:
    reasons = attrs.get("job-state-reasons") or []
    if isinstance(reasons, str):
        reasons = [reasons]
    mapped = _JOB_STATE_MAP.get(attrs.get("job-state"), "UNKNOWN")
    if mapped in ("PENDING", "PROCESSING") and any(reason.endswith("-error") for reason in reasons):
        return "FAILED"
    return mapped


def _epoch_to_iso(value) -> Optional[str]:
    if not value:
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()


def _job_error_message(attrs: dict, status: str) -> Optional[str]:
    if status != "FAILED":
        return None
    reasons = attrs.get("job-state-reasons") or []
    if isinstance(reasons, str):
        reasons = [reasons]
    error_reasons = [reason for reason in reasons if reason.endswith("-error")]
    return ", ".join(error_reasons) if error_reasons else "Job failed"


def _to_summary(job_id: int, attrs: dict) -> dict:
    return {
        "job_id": job_id,
        "printer": printer_name_from_uri(attrs.get("job-printer-uri", "")),
        "document": attrs.get("job-name", ""),
        "user": attrs.get("job-originating-user-name", ""),
        "submitted_at": _epoch_to_iso(attrs.get("time-at-creation")),
        "status": map_job_state(attrs),
    }


class JobService:
    def __init__(self, cups_service: CupsService):
        self._cups = cups_service

    def list_jobs(self, printer: Optional[str] = None) -> list[dict]:
        jobs = self._cups.list_jobs(which_jobs="all")
        summaries = [_to_summary(job_id, attrs) for job_id, attrs in jobs.items()]
        if printer:
            summaries = [job for job in summaries if job["printer"] == printer]
        summaries.sort(key=lambda job: job["job_id"], reverse=True)
        return summaries

    def get_job(self, job_id: int) -> dict:
        attrs = self._cups.get_job(job_id)  # raises JobNotFoundError
        status = map_job_state(attrs)
        summary = _to_summary(job_id, attrs)
        summary.update(
            {
                "owner": attrs.get("job-originating-user-name", ""),
                "started_at": _epoch_to_iso(attrs.get("time-at-processing")),
                "completed_at": _epoch_to_iso(attrs.get("time-at-completed")),
                "options": {key: str(attrs[key]) for key in _OPTION_ATTRS if key in attrs},
                "error": _job_error_message(attrs, status),
            }
        )
        return summary

    def cancel_job(self, job_id: int) -> None:
        attrs = self._cups.get_job(job_id)  # raises JobNotFoundError
        status = map_job_state(attrs)
        if status in _TERMINAL_STATES:
            raise JobNotCancelableError(f"Job {job_id} is already {status.lower()} and cannot be canceled")
        self._cups.cancel_job(job_id)
