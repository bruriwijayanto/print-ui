"""Maps raw CUPS/IPP attribute dicts to the shapes the API exposes.

All "what does this IPP attribute mean" logic lives here so routes and
schemas stay dumb, and cups.py stays a thin CUPS/IPP wrapper.
"""

from __future__ import annotations

from app.services.cups import CupsService

# IPP printer-state values (RFC 8011).
_IPP_STATE_IDLE = 3
_IPP_STATE_PROCESSING = 4
_IPP_STATE_STOPPED = 5

_STATE_MAP = {
    _IPP_STATE_IDLE: "IDLE",
    _IPP_STATE_PROCESSING: "PRINTING",
    _IPP_STATE_STOPPED: "STOPPED",
}

# not-completed IPP job-state values.
_JOB_STATE_PROCESSING = 5


def map_printer_state(attrs: dict) -> str:
    reasons = attrs.get("printer-state-reasons") or []
    if isinstance(reasons, str):
        reasons = [reasons]
    if any(reason.endswith("-error") for reason in reasons):
        return "ERROR"
    raw_state = attrs.get("printer-state")
    return _STATE_MAP.get(raw_state, "UNKNOWN")


def _printer_name_from_uri(uri: str) -> str:
    return uri.rstrip("/").rsplit("/", 1)[-1]


def _job_counts_by_printer(cups_service: CupsService) -> dict[str, dict]:
    """Returns {printer_name: {"queue_count": int, "current_job": int | None}}."""
    jobs = cups_service.list_jobs(which_jobs="not-completed")
    counts: dict[str, dict] = {}
    for job_id, job_attrs in jobs.items():
        printer_uri = job_attrs.get("job-printer-uri", "")
        if not printer_uri:
            continue
        printer_name = _printer_name_from_uri(printer_uri)
        entry = counts.setdefault(printer_name, {"queue_count": 0, "current_job": None})
        entry["queue_count"] += 1
        if job_attrs.get("job-state") == _JOB_STATE_PROCESSING:
            entry["current_job"] = job_id
    return counts


def _to_summary(name: str, attrs: dict, job_info: dict) -> dict:
    return {
        "name": name,
        "description": attrs.get("printer-info", ""),
        "state": map_printer_state(attrs),
        "state_message": attrs.get("printer-state-message", ""),
        "accepting_jobs": bool(attrs.get("printer-is-accepting-jobs", False)),
        "shared": bool(attrs.get("printer-is-shared", False)),
        "device_uri": attrs.get("device-uri"),
        "current_job": job_info.get("current_job"),
        "queue_count": job_info.get("queue_count", 0),
    }


def _to_capabilities(attrs: dict) -> dict:
    media = attrs.get("media-supported") or []
    if isinstance(media, str):
        media = [media]
    resolutions = attrs.get("printer-resolution-supported") or []
    if isinstance(resolutions, tuple):
        resolutions = [resolutions]
    resolution_labels = [
        f"{res[0]}x{res[1]} {'dpi' if res[2] == 3 else 'dpc'}" if isinstance(res, tuple) else str(res)
        for res in resolutions
    ]
    color_modes = attrs.get("print-color-mode-supported") or attrs.get("urf-supported") or []
    sides = attrs.get("sides-supported") or []

    return {
        "media": list(media),
        "color": "color" in color_modes if color_modes else bool(attrs.get("color-supported", False)),
        "duplex": any(side != "one-sided" for side in sides) if sides else False,
        "resolution": resolution_labels,
        "copies_supported": "copies-supported" in attrs,
        "max_copies": attrs.get("copies-supported") if isinstance(attrs.get("copies-supported"), int) else None,
        "page_ranges_supported": bool(attrs.get("page-ranges-supported", False)),
        "orientation_supported": "orientation-requested-supported" in attrs,
    }


class PrinterService:
    def __init__(self, cups_service: CupsService):
        self._cups = cups_service

    def list_printers(self) -> list[dict]:
        # getPrinters() only returns a reduced attribute set (notably missing
        # printer-is-accepting-jobs), so it is used only to enumerate names —
        # getPrinterAttributes() is the accurate, full source used everywhere.
        printer_names = self._cups.list_printers().keys()
        job_counts = _job_counts_by_printer(self._cups)
        result = []
        for name in printer_names:
            attrs = self._cups.get_printer_attributes(name)
            result.append(_to_summary(name, attrs, job_counts.get(name, {})))
        return result

    def get_printer(self, name: str) -> dict:
        attrs = self._cups.get_printer_attributes(name)
        job_counts = _job_counts_by_printer(self._cups)
        summary = _to_summary(name, attrs, job_counts.get(name, {}))
        summary.update(
            {
                "location": attrs.get("printer-location"),
                "manufacturer": (attrs.get("printer-make-and-model") or "").split(" ")[0] or None,
                "model": attrs.get("printer-make-and-model"),
                "capabilities": _to_capabilities(attrs),
            }
        )
        return summary
