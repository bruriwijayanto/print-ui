from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.dependencies import get_print_service
from app.schemas.print import PrintJobResponse
from app.services.cups import CupsConnectionError, CupsOperationError, PrinterNotFoundError
from app.services.print_service import PrinterNotAcceptingJobsError, PrintService
from app.utils.files import FileTooLargeError, InvalidFileError

router = APIRouter(tags=["print"])

_PAGE_RANGES_PATTERN = r"^[0-9]+(-[0-9]+)?(,[0-9]+(-[0-9]+)?)*$"


@router.post("/print", response_model=PrintJobResponse)
async def print_document(
    file: UploadFile = File(...),
    printer: str = Form(...),
    copies: int = Form(1, ge=1, le=999),
    page_ranges: Optional[str] = Form(None, pattern=_PAGE_RANGES_PATTERN),
    media: Optional[str] = Form(None, max_length=64),
    orientation: Optional[str] = Form(None, max_length=64),
    color: Optional[str] = Form(None, max_length=64),
    duplex: Optional[str] = Form(None, max_length=64),
    print_service: PrintService = Depends(get_print_service),
):
    try:
        return await print_service.submit_print(
            printer=printer,
            file=file,
            copies=copies,
            page_ranges=page_ranges,
            media=media,
            orientation=orientation,
            color=color,
            duplex=duplex,
        )
    except PrinterNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"code": "PRINTER_NOT_FOUND", "message": str(exc)}) from exc
    except PrinterNotAcceptingJobsError as exc:
        raise HTTPException(status_code=409, detail={"code": exc.code, "message": str(exc)}) from exc
    except InvalidFileError as exc:
        raise HTTPException(status_code=400, detail={"code": "INVALID_FILE", "message": str(exc)}) from exc
    except FileTooLargeError as exc:
        raise HTTPException(status_code=413, detail={"code": "FILE_TOO_LARGE", "message": str(exc)}) from exc
    except CupsConnectionError as exc:
        raise HTTPException(status_code=503, detail={"code": "CUPS_UNAVAILABLE", "message": str(exc)}) from exc
    except CupsOperationError as exc:
        raise HTTPException(status_code=502, detail={"code": "PRINT_FAILED", "message": str(exc)}) from exc
