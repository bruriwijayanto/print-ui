from fastapi.testclient import TestClient

from app.dependencies import get_printer_service
from app.main import app
from app.services.cups import CupsConnectionError, PrinterNotFoundError

_PRINTER = {
    "name": "DevTestPrinter",
    "description": "Generic test printer",
    "state": "IDLE",
    "state_message": "",
    "accepting_jobs": True,
    "shared": True,
    "device_uri": "file:///dev/null",
    "current_job": None,
    "queue_count": 0,
}

_PRINTER_DETAIL = {
    **_PRINTER,
    "location": "Dev Lab",
    "manufacturer": "Generic",
    "model": "Generic PostScript Printer",
    "capabilities": {
        "media": ["iso_a4_210x297mm"],
        "color": True,
        "duplex": False,
        "resolution": ["300x300 dpi"],
        "copies_supported": True,
        "max_copies": None,
        "page_ranges_supported": True,
        "orientation_supported": True,
    },
}


class _FakePrinterService:
    def __init__(self, printers=None, detail=None, error=None):
        self._printers = printers or []
        self._detail = detail
        self._error = error

    def list_printers(self):
        if self._error:
            raise self._error
        return self._printers

    def get_printer(self, name):
        if self._error:
            raise self._error
        if self._detail is None:
            raise PrinterNotFoundError(f"Printer '{name}' not found")
        return self._detail


def teardown_function():
    app.dependency_overrides.clear()


def test_list_printers_returns_data_from_cups():
    app.dependency_overrides[get_printer_service] = lambda: _FakePrinterService(printers=[_PRINTER])
    client = TestClient(app)

    response = client.get("/api/printers")

    assert response.status_code == 200
    assert response.json() == [_PRINTER]


def test_list_printers_returns_503_when_cups_unreachable():
    app.dependency_overrides[get_printer_service] = lambda: _FakePrinterService(
        error=CupsConnectionError("down")
    )
    client = TestClient(app)

    response = client.get("/api/printers")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "CUPS_UNAVAILABLE"


def test_get_printer_detail():
    app.dependency_overrides[get_printer_service] = lambda: _FakePrinterService(detail=_PRINTER_DETAIL)
    client = TestClient(app)

    response = client.get("/api/printers/DevTestPrinter")

    assert response.status_code == 200
    assert response.json() == _PRINTER_DETAIL


def test_get_printer_not_found_returns_404():
    app.dependency_overrides[get_printer_service] = lambda: _FakePrinterService()
    client = TestClient(app)

    response = client.get("/api/printers/DoesNotExist")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PRINTER_NOT_FOUND"
