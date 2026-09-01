from functools import lru_cache

from app.config import get_settings
from app.services.cups import CupsService
from app.services.printer_service import PrinterService


@lru_cache
def get_cups_service() -> CupsService:
    settings = get_settings()
    return CupsService(settings.cups_server, settings.cups_user, settings.cups_password)


def get_printer_service() -> PrinterService:
    return PrinterService(get_cups_service())
