"""Stricter, dedicated rate limit for login attempts.

Separate from the general RateLimitMiddleware: a user-chosen password is
far more guessable than the 32-byte random PRINT_API_KEY, so brute-force
attempts need a tighter budget than the general API traffic limit.
"""

from __future__ import annotations

import time
from collections import deque

from fastapi import HTTPException, Request

from app.middleware.rate_limit import client_ip

MAX_ATTEMPTS = 10
WINDOW_SECONDS = 300.0  # 5 minutes

_attempts: dict[str, deque[float]] = {}


def enforce_login_rate_limit(request: Request) -> None:
    ip = client_ip(request)
    now = time.monotonic()
    hits = _attempts.setdefault(ip, deque())

    while hits and now - hits[0] > WINDOW_SECONDS:
        hits.popleft()

    if len(hits) >= MAX_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail={"code": "TOO_MANY_LOGIN_ATTEMPTS", "message": "Too many login attempts, try again later"},
        )

    hits.append(now)
