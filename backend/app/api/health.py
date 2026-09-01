from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.dependencies import get_printer_service
from app.services.cups import CupsConnectionError, CupsOperationError
from app.services.printer_service import PrinterService

router = APIRouter(tags=["health"])


@router.get("/health")
def health(printer_service: PrinterService = Depends(get_printer_service)):
    try:
        printers = printer_service.list_printers()
        return {"status": "ok", "cups": "connected", "printers": len(printers)}
    except (CupsConnectionError, CupsOperationError):
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "cups": "disconnected"},
        )
