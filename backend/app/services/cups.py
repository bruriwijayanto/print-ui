"""Low-level wrapper around the CUPS server via pycups (IPP).

This module only speaks CUPS/IPP. It knows nothing about FastAPI, HTTP
status codes, or the app's response schemas — that mapping lives in
printer_service.py / print_service.py.
"""

from __future__ import annotations

from urllib.parse import urlparse

import cups


class CupsConnectionError(Exception):
    """Raised when the CUPS server cannot be reached at all."""


class CupsOperationError(Exception):
    """Raised when CUPS reached but rejected/failed an operation."""


class PrinterNotFoundError(Exception):
    """Raised when a printer name does not exist on the CUPS server."""


class JobNotFoundError(Exception):
    """Raised when a job id does not exist on the CUPS server."""


class CupsService:
    def __init__(self, server_url: str, user: str = "", password: str = ""):
        parsed = urlparse(server_url)
        self._host = parsed.hostname or "localhost"
        self._port = parsed.port or 631
        self._user = user
        self._password = password

    def _connect(self) -> cups.Connection:
        cups.setServer(self._host)
        cups.setPort(self._port)
        if self._user:
            cups.setUser(self._user)
            cups.setPasswordCB(lambda prompt: self._password)
        try:
            return cups.Connection()
        except RuntimeError as exc:
            raise CupsConnectionError(
                f"Unable to connect to CUPS server at {self._host}:{self._port}: {exc}"
            ) from exc

    # -- printers ---------------------------------------------------------

    def list_printers(self) -> dict[str, dict]:
        conn = self._connect()
        try:
            return conn.getPrinters()
        except cups.IPPError as exc:
            raise CupsOperationError(str(exc)) from exc

    def get_printer_attributes(self, name: str) -> dict:
        conn = self._connect()
        try:
            return conn.getPrinterAttributes(name)
        except cups.IPPError as exc:
            raise PrinterNotFoundError(f"Printer '{name}' not found") from exc

    def pause_printer(self, name: str) -> None:
        conn = self._connect()
        try:
            conn.disablePrinter(name, reason="Paused via CUPS Print Manager")
        except cups.IPPError as exc:
            raise CupsOperationError(str(exc)) from exc

    def resume_printer(self, name: str) -> None:
        conn = self._connect()
        try:
            conn.enablePrinter(name)
        except cups.IPPError as exc:
            raise CupsOperationError(str(exc)) from exc

    def enable_printer(self, name: str) -> None:
        """Allow the printer to accept new jobs into its queue."""
        conn = self._connect()
        try:
            conn.acceptJobs(name)
        except cups.IPPError as exc:
            raise CupsOperationError(str(exc)) from exc

    def disable_printer(self, name: str) -> None:
        """Stop the printer from accepting new jobs into its queue."""
        conn = self._connect()
        try:
            conn.rejectJobs(name, reason="Disabled via CUPS Print Manager")
        except cups.IPPError as exc:
            raise CupsOperationError(str(exc)) from exc

    # -- jobs ---------------------------------------------------------------

    def list_jobs(self, which_jobs: str = "not-completed") -> dict[int, dict]:
        conn = self._connect()
        try:
            return conn.getJobs(which_jobs=which_jobs, my_jobs=False)
        except cups.IPPError as exc:
            raise CupsOperationError(str(exc)) from exc

    def get_job(self, job_id: int) -> dict:
        conn = self._connect()
        try:
            return conn.getJobAttributes(job_id)
        except cups.IPPError as exc:
            raise JobNotFoundError(f"Job '{job_id}' not found") from exc

    def cancel_job(self, job_id: int) -> None:
        conn = self._connect()
        try:
            conn.cancelJob(job_id)
        except cups.IPPError as exc:
            raise CupsOperationError(str(exc)) from exc

    def submit_print_job(
        self,
        printer: str,
        file_path: str,
        title: str,
        options: dict[str, str],
    ) -> int:
        conn = self._connect()
        try:
            return conn.printFile(printer, file_path, title, options)
        except cups.IPPError as exc:
            raise CupsOperationError(str(exc)) from exc
