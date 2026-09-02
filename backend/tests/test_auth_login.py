from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def teardown_function():
    app.dependency_overrides.clear()


def test_login_success_returns_token():
    settings = get_settings()
    client = TestClient(app)

    response = client.post(
        "/api/auth/login",
        json={"username": settings.admin_username, "password": settings.admin_password},
    )

    assert response.status_code == 200
    assert response.json() == {"token": settings.print_api_key}


def test_login_rejects_wrong_password():
    settings = get_settings()
    client = TestClient(app)

    response = client.post(
        "/api/auth/login",
        json={"username": settings.admin_username, "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "INVALID_CREDENTIALS"


def test_login_rejects_wrong_username():
    settings = get_settings()
    client = TestClient(app)

    response = client.post(
        "/api/auth/login",
        json={"username": "not-admin", "password": settings.admin_password},
    )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "INVALID_CREDENTIALS"


def test_login_is_rate_limited_after_too_many_attempts():
    settings = get_settings()
    client = TestClient(app, headers={"X-Forwarded-For": "203.0.113.55"})

    for _ in range(10):
        client.post("/api/auth/login", json={"username": "x", "password": "y"})

    response = client.post(
        "/api/auth/login",
        json={"username": settings.admin_username, "password": settings.admin_password},
    )

    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "TOO_MANY_LOGIN_ATTEMPTS"
