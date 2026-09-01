import time

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.rate_limit import RateLimitMiddleware


def _build_app(max_requests: int = 3, window_seconds: float = 60.0) -> FastAPI:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, max_requests=max_requests, window_seconds=window_seconds)

    @app.get("/api/ping")
    def ping():
        return {"pong": True}

    @app.get("/health")
    def health():
        return {"ok": True}

    return app


def test_allows_requests_under_the_limit():
    client = TestClient(_build_app(max_requests=3))

    for _ in range(3):
        response = client.get("/api/ping")
        assert response.status_code == 200


def test_blocks_requests_over_the_limit():
    client = TestClient(_build_app(max_requests=3))

    for _ in range(3):
        client.get("/api/ping")

    response = client.get("/api/ping")

    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "RATE_LIMITED"


def test_does_not_rate_limit_non_api_paths():
    client = TestClient(_build_app(max_requests=1))

    client.get("/api/ping")  # consumes the one allowed /api/ slot
    response = client.get("/health")

    assert response.status_code == 200


def test_tracks_clients_independently_by_forwarded_for():
    client = TestClient(_build_app(max_requests=1))

    r1 = client.get("/api/ping", headers={"X-Forwarded-For": "1.1.1.1"})
    r2 = client.get("/api/ping", headers={"X-Forwarded-For": "2.2.2.2"})

    assert r1.status_code == 200
    assert r2.status_code == 200


def test_window_resets_after_expiry():
    client = TestClient(_build_app(max_requests=1, window_seconds=0.05))

    assert client.get("/api/ping").status_code == 200
    assert client.get("/api/ping").status_code == 429

    time.sleep(0.1)

    assert client.get("/api/ping").status_code == 200
