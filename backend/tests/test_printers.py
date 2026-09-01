from fastapi.testclient import TestClient

from app.dependencies import get_cups_service, get_printer_service
from app.main import app
from app.services.cups import CupsConnectionError, CupsOperationError, PrinterNotFoundError

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


class _FakeCupsService:
    def __init__(self, error=None):
        self._error = error
        self.calls = []

    def _do(self, action, name):
        self.calls.append((action, name))
        if self._error:
            raise self._error

    def pause_printer(self, name):
        self._do("pause", name)

    def resume_printer(self, name):
        self._do("resume", name)

    def enable_printer(self, name):
        self._do("enable", name)

    def disable_printer(self, name):
        self._do("disable", name)


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


def test_pause_printer_success():
    fake = _FakeCupsService()
    app.dependency_overrides[get_cups_service] = lambda: fake
    client = TestClient(app)

    response = client.post("/api/printers/Canon-G2030/pause")

    assert response.status_code == 200
    assert response.json() == {"success": True, "printer": "Canon-G2030", "action": "paused"}
    assert fake.calls == [("pause", "Canon-G2030")]


def test_resume_printer_success():
    fake = _FakeCupsService()
    app.dependency_overrides[get_cups_service] = lambda: fake
    client = TestClient(app)

    response = client.post("/api/printers/Canon-G2030/resume")

    assert response.status_code == 200
    assert response.json()["action"] == "resumed"


def test_enable_printer_success():
    fake = _FakeCupsService()
    app.dependency_overrides[get_cups_service] = lambda: fake
    client = TestClient(app)

    response = client.post("/api/printers/Canon-G2030/enable")

    assert response.status_code == 200
    assert response.json()["action"] == "enabled"


def test_disable_printer_success():
    fake = _FakeCupsService()
    app.dependency_overrides[get_cups_service] = lambda: fake
    client = TestClient(app)

    response = client.post("/api/printers/Canon-G2030/disable")

    assert response.status_code == 200
    assert response.json()["action"] == "disabled"


def test_pause_printer_cups_unavailable():
    app.dependency_overrides[get_cups_service] = lambda: _FakeCupsService(error=CupsConnectionError("down"))
    client = TestClient(app)

    response = client.post("/api/printers/Canon-G2030/pause")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "CUPS_UNAVAILABLE"


def test_pause_printer_cups_operation_error():
    app.dependency_overrides[get_cups_service] = lambda: _FakeCupsService(error=CupsOperationError("rejected"))
    client = TestClient(app)

    response = client.post("/api/printers/Canon-G2030/pause")

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "CUPS_ERROR"
