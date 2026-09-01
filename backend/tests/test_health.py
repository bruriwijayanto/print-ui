from fastapi.testclient import TestClient

from app.dependencies import get_printer_service
from app.main import app
from app.services.cups import CupsConnectionError


class _FakePrinterServiceUp:
    def list_printers(self):
        return [
            {
                "name": "DevTestPrinter",
                "description": "",
                "state": "IDLE",
                "state_message": "",
                "accepting_jobs": True,
                "shared": False,
                "device_uri": None,
                "current_job": None,
                "queue_count": 0,
            }
        ]


class _FakePrinterServiceDown:
    def list_printers(self):
        raise CupsConnectionError("cups unreachable")


def teardown_function():
    app.dependency_overrides.clear()


def test_health_ok_when_cups_connected():
    app.dependency_overrides[get_printer_service] = lambda: _FakePrinterServiceUp()
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "cups": "connected", "printers": 1}


def test_health_degraded_when_cups_unreachable():
    app.dependency_overrides[get_printer_service] = lambda: _FakePrinterServiceDown()
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "cups": "disconnected"}
