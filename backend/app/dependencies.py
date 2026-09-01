import secrets
from functools import lru_cache
from typing import Optional

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings
from app.services.cups import CupsService
from app.services.job_service import JobService
from app.services.print_service import PrintService
from app.services.printer_service import PrinterService

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer_scheme),
) -> str:
    settings = get_settings()
    provided = credentials.credentials if credentials else ""
    if not provided or not secrets.compare_digest(provided, settings.print_api_key):
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Invalid or missing API key"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return provided


@lru_cache
def get_cups_service() -> CupsService:
    settings = get_settings()
    return CupsService(settings.cups_server, settings.cups_user, settings.cups_password)


def get_printer_service() -> PrinterService:
    return PrinterService(get_cups_service())


def get_print_service() -> PrintService:
    settings = get_settings()
    return PrintService(get_cups_service(), settings.max_upload_size_bytes)


def get_job_service() -> JobService:
    return JobService(get_cups_service())
