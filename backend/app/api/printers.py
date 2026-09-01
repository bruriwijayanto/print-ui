from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_cups_service, get_job_service, get_printer_service
from app.schemas.job import JobSummary
from app.schemas.printer import PrinterDetail, PrinterSummary
from app.schemas.printer_action import PrinterActionResponse
from app.services.cups import CupsConnectionError, CupsOperationError, CupsService, PrinterNotFoundError
from app.services.job_service import JobService
from app.services.printer_service import PrinterService

router = APIRouter(prefix="/printers", tags=["printers"])


def _handle_action(printer_name: str, action: str, operation) -> PrinterActionResponse:
    try:
        operation()
        return PrinterActionResponse(printer=printer_name, action=action)
    except CupsConnectionError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "CUPS_UNAVAILABLE", "message": str(exc)},
        ) from exc
    except CupsOperationError as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": "CUPS_ERROR", "message": str(exc)},
        ) from exc


@router.get("", response_model=list[PrinterSummary])
def list_printers(printer_service: PrinterService = Depends(get_printer_service)):
    try:
        return printer_service.list_printers()
    except CupsConnectionError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "CUPS_UNAVAILABLE", "message": str(exc)},
        ) from exc
    except CupsOperationError as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": "CUPS_ERROR", "message": str(exc)},
        ) from exc


@router.get("/{printer_name}/jobs", response_model=list[JobSummary])
def list_printer_jobs(
    printer_name: str,
    printer_service: PrinterService = Depends(get_printer_service),
    job_service: JobService = Depends(get_job_service),
):
    try:
        printer_service.get_printer(printer_name)  # existence check; raises PrinterNotFoundError
        return job_service.list_jobs(printer=printer_name)
    except PrinterNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "PRINTER_NOT_FOUND", "message": str(exc)},
        ) from exc
    except CupsConnectionError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "CUPS_UNAVAILABLE", "message": str(exc)},
        ) from exc
    except CupsOperationError as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": "CUPS_ERROR", "message": str(exc)},
        ) from exc


@router.post("/{printer_name}/pause", response_model=PrinterActionResponse)
def pause_printer(printer_name: str, cups_service: CupsService = Depends(get_cups_service)):
    return _handle_action(printer_name, "paused", lambda: cups_service.pause_printer(printer_name))


@router.post("/{printer_name}/resume", response_model=PrinterActionResponse)
def resume_printer(printer_name: str, cups_service: CupsService = Depends(get_cups_service)):
    return _handle_action(printer_name, "resumed", lambda: cups_service.resume_printer(printer_name))


@router.post("/{printer_name}/enable", response_model=PrinterActionResponse)
def enable_printer(printer_name: str, cups_service: CupsService = Depends(get_cups_service)):
    return _handle_action(printer_name, "enabled", lambda: cups_service.enable_printer(printer_name))


@router.post("/{printer_name}/disable", response_model=PrinterActionResponse)
def disable_printer(printer_name: str, cups_service: CupsService = Depends(get_cups_service)):
    return _handle_action(printer_name, "disabled", lambda: cups_service.disable_printer(printer_name))


@router.get("/{printer_name}", response_model=PrinterDetail)
def get_printer(printer_name: str, printer_service: PrinterService = Depends(get_printer_service)):
    try:
        return printer_service.get_printer(printer_name)
    except PrinterNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "PRINTER_NOT_FOUND", "message": str(exc)},
        ) from exc
    except CupsConnectionError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "CUPS_UNAVAILABLE", "message": str(exc)},
        ) from exc
    except CupsOperationError as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": "CUPS_ERROR", "message": str(exc)},
        ) from exc
