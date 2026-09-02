from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, health, jobs, print as print_api, printers
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
# /api/health and /api/auth/login stay unauthenticated by design: health is
# polled by Docker's own HEALTHCHECK without credentials, and login is how a
# client obtains credentials in the first place. Login has its own, stricter
# rate limit (see login_rate_limit.py) since a user-chosen password is more
# guessable than the random PRINT_API_KEY the other routers require.
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(printers.router, dependencies=[Depends(get_current_api_key)])
api_router.include_router(print_api.router, dependencies=[Depends(get_current_api_key)])
api_router.include_router(jobs.router, dependencies=[Depends(get_current_api_key)])

app.include_router(api_router)
