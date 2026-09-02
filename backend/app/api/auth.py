import secrets

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.middleware.login_rate_limit import enforce_login_rate_limit
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=LoginResponse, dependencies=[Depends(enforce_login_rate_limit)])
def login(payload: LoginRequest, settings: Settings = Depends(get_settings)):
    username_ok = secrets.compare_digest(payload.username, settings.admin_username)
    password_ok = secrets.compare_digest(payload.password, settings.admin_password)
    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid username or password"},
        )
    return LoginResponse(token=settings.print_api_key)
