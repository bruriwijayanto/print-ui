from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_job_service, get_printer_service
from app.schemas.job import JobSummary
from app.schemas.printer import PrinterDetail, PrinterSummary
from app.services.cups import CupsConnectionError, CupsOperationError, PrinterNotFoundError
from app.services.job_service import JobService
from app.services.printer_service import PrinterService

router = APIRouter(prefix="/printers", tags=["printers"])


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
