from fastapi.testclient import TestClient

from app.config import get_settings
from app.dependencies import get_current_api_key, get_printer_service
from app.main import app


class _FakePrinterService:
    def list_printers(self):
        return []


def teardown_function():
    app.dependency_overrides.clear()


def test_protected_endpoint_rejects_missing_api_key():
    app.dependency_overrides.pop(get_current_api_key, None)
    client = TestClient(app)

    response = client.get("/api/printers")

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "UNAUTHORIZED"


def test_protected_endpoint_rejects_wrong_api_key():
    app.dependency_overrides.pop(get_current_api_key, None)
    client = TestClient(app)

    response = client.get("/api/printers", headers={"Authorization": "Bearer wrong-key"})

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "UNAUTHORIZED"


def test_protected_endpoint_accepts_correct_api_key():
    app.dependency_overrides.pop(get_current_api_key, None)
    app.dependency_overrides[get_printer_service] = lambda: _FakePrinterService()
    settings = get_settings()
    client = TestClient(app)

    response = client.get("/api/printers", headers={"Authorization": f"Bearer {settings.print_api_key}"})

    assert response.status_code == 200
    assert response.json() == []


def test_health_does_not_require_api_key():
    app.dependency_overrides.pop(get_current_api_key, None)
    client = TestClient(app)

    response = client.get("/api/health")

    # Reachable regardless of CUPS connectivity (200 or 503) — never blocked by auth.
    assert response.status_code != 401
