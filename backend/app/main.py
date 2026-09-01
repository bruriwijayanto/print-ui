from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, print as print_api, printers
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="CUPS Print Manager API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(printers.router)
api_router.include_router(print_api.router)

app.include_router(api_router)
