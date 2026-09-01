"""Simple in-memory rate limiting — no Redis, no external dependency.

Good enough for a single-process STB deployment: one uvicorn worker means
the in-memory counters are authoritative. This intentionally does not try
to be a precise login-attempt lockout — the API key is a 32-byte random
value (infeasible to brute force regardless of rate), so this exists to
absorb runaway/misbehaving clients and casual abuse, not targeted attacks.
"""

from __future__ import annotations

import time
from collections import deque

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 180, window_seconds: float = 60.0):
        super().__init__(app)
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = {}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        client_ip = _client_ip(request)
        now = time.monotonic()
        hits = self._hits.setdefault(client_ip, deque())

        while hits and now - hits[0] > self._window_seconds:
            hits.popleft()

        if len(hits) >= self._max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": {"code": "RATE_LIMITED", "message": "Too many requests, slow down"}},
            )

        hits.append(now)
        return await call_next(request)
