from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, jobs, print as print_api, printers
from app.config import get_settings
from app.dependencies import get_current_api_key
from app.middleware.rate_limit import RateLimitMiddleware

settings = get_settings()

app = FastAPI(title="CUPS Print Manager API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware, max_requests=180, window_seconds=60)

api_router = APIRouter(prefix="/api")
# /api/health stays unauthenticated: Docker's own HEALTHCHECK and uptime
# monitors call it without credentials, and it exposes no sensitive data.
api_router.include_router(health.router)
api_router.include_router(printers.router, dependencies=[Depends(get_current_api_key)])
api_router.include_router(print_api.router, dependencies=[Depends(get_current_api_key)])
api_router.include_router(jobs.router, dependencies=[Depends(get_current_api_key)])

app.include_router(api_router)
