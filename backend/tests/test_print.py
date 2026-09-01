from fastapi.testclient import TestClient

from app.dependencies import get_print_service
from app.main import app
from app.services.cups import CupsConnectionError, CupsOperationError, PrinterNotFoundError
from app.services.print_service import PrinterNotAcceptingJobsError
from app.utils.files import FileTooLargeError, InvalidFileError

_JOB_RESPONSE = {
    "success": True,
    "job_id": 42,
    "printer": "Canon-G2030",
    "filename": "test.pdf",
    "status": "queued",
}


class _FakePrintService:
    def __init__(self, response=None, error=None):
        self._response = response
        self._error = error

    async def submit_print(self, **kwargs):
        if self._error:
            raise self._error
        return self._response


def teardown_function():
    app.dependency_overrides.clear()


def _post_print(client: TestClient, **form_overrides):
    files = {"file": ("test.pdf", b"%PDF-1.4 fake pdf content", "application/pdf")}
    data = {"printer": "Canon-G2030", "copies": "1"}
    data.update(form_overrides)
    return client.post("/api/print", files=files, data=data)


def test_print_document_success():
    app.dependency_overrides[get_print_service] = lambda: _FakePrintService(response=_JOB_RESPONSE)
    client = TestClient(app)

    response = _post_print(client)

    assert response.status_code == 200
    assert response.json() == _JOB_RESPONSE


def test_print_document_printer_not_found():
    app.dependency_overrides[get_print_service] = lambda: _FakePrintService(
        error=PrinterNotFoundError("Printer 'X' not found")
    )
    client = TestClient(app)

    response = _post_print(client)

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PRINTER_NOT_FOUND"


def test_print_document_printer_stopped():
    app.dependency_overrides[get_print_service] = lambda: _FakePrintService(
        error=PrinterNotAcceptingJobsError("PRINTER_STOPPED", "Printer is stopped")
    )
    client = TestClient(app)

    response = _post_print(client)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "PRINTER_STOPPED"


def test_print_document_invalid_file():
    app.dependency_overrides[get_print_service] = lambda: _FakePrintService(
        error=InvalidFileError("bad file")
    )
    client = TestClient(app)

    response = _post_print(client)

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_FILE"


def test_print_document_file_too_large():
    app.dependency_overrides[get_print_service] = lambda: _FakePrintService(
        error=FileTooLargeError("too big")
    )
    client = TestClient(app)

    response = _post_print(client)

    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "FILE_TOO_LARGE"


def test_print_document_cups_unavailable():
    app.dependency_overrides[get_print_service] = lambda: _FakePrintService(
        error=CupsConnectionError("down")
    )
    client = TestClient(app)

    response = _post_print(client)

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "CUPS_UNAVAILABLE"


def test_print_document_cups_operation_error():
    app.dependency_overrides[get_print_service] = lambda: _FakePrintService(
        error=CupsOperationError("rejected")
    )
    client = TestClient(app)

    response = _post_print(client)

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "PRINT_FAILED"


def test_print_document_rejects_invalid_copies():
    app.dependency_overrides[get_print_service] = lambda: _FakePrintService(response=_JOB_RESPONSE)
    client = TestClient(app)

    response = _post_print(client, copies="0")

    assert response.status_code == 422


def test_print_document_rejects_invalid_page_ranges():
    app.dependency_overrides[get_print_service] = lambda: _FakePrintService(response=_JOB_RESPONSE)
    client = TestClient(app)

    response = _post_print(client, page_ranges="'; DROP TABLE jobs;--")

    assert response.status_code == 422
