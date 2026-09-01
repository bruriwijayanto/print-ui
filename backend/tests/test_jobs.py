from fastapi.testclient import TestClient

from app.dependencies import get_job_service, get_printer_service
from app.main import app
from app.services.cups import CupsConnectionError, JobNotFoundError, PrinterNotFoundError
from app.services.job_service import JobNotCancelableError

_JOB_SUMMARY = {
    "job_id": 3,
    "printer": "Canon-G2030",
    "document": "kartutes.pdf",
    "user": "root",
    "submitted_at": "2026-09-01T08:19:21+00:00",
    "status": "COMPLETED",
}

_JOB_DETAIL = {
    **_JOB_SUMMARY,
    "owner": "root",
    "started_at": "2026-09-01T08:19:22+00:00",
    "completed_at": "2026-09-01T08:19:30+00:00",
    "options": {"copies": "1"},
    "error": None,
}


class _FakeJobService:
    def __init__(self, jobs=None, detail=None, error=None, cancel_error=None):
        self._jobs = jobs or []
        self._detail = detail
        self._error = error
        self._cancel_error = cancel_error

    def list_jobs(self, printer=None):
        if self._error:
            raise self._error
        if printer:
            return [job for job in self._jobs if job["printer"] == printer]
        return self._jobs

    def get_job(self, job_id):
        if self._error:
            raise self._error
        if self._detail is None:
            raise JobNotFoundError(f"Job '{job_id}' not found")
        return self._detail

    def cancel_job(self, job_id):
        if self._cancel_error:
            raise self._cancel_error


class _FakePrinterService:
    def __init__(self, exists=True):
        self._exists = exists

    def get_printer(self, name):
        if not self._exists:
            raise PrinterNotFoundError(f"Printer '{name}' not found")
        return {"name": name}


def teardown_function():
    app.dependency_overrides.clear()


def test_list_jobs_returns_data_from_cups():
    app.dependency_overrides[get_job_service] = lambda: _FakeJobService(jobs=[_JOB_SUMMARY])
    client = TestClient(app)

    response = client.get("/api/jobs")

    assert response.status_code == 200
    assert response.json() == [_JOB_SUMMARY]


def test_list_jobs_returns_503_when_cups_unreachable():
    app.dependency_overrides[get_job_service] = lambda: _FakeJobService(error=CupsConnectionError("down"))
    client = TestClient(app)

    response = client.get("/api/jobs")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "CUPS_UNAVAILABLE"


def test_get_job_detail():
    app.dependency_overrides[get_job_service] = lambda: _FakeJobService(detail=_JOB_DETAIL)
    client = TestClient(app)

    response = client.get("/api/jobs/3")

    assert response.status_code == 200
    assert response.json() == _JOB_DETAIL


def test_get_job_not_found_returns_404():
    app.dependency_overrides[get_job_service] = lambda: _FakeJobService()
    client = TestClient(app)

    response = client.get("/api/jobs/999")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "JOB_NOT_FOUND"


def test_cancel_job_success():
    app.dependency_overrides[get_job_service] = lambda: _FakeJobService()
    client = TestClient(app)

    response = client.delete("/api/jobs/3")

    assert response.status_code == 200
    assert response.json() == {"success": True, "job_id": 3, "status": "canceled"}


def test_cancel_job_not_found():
    app.dependency_overrides[get_job_service] = lambda: _FakeJobService(
        cancel_error=JobNotFoundError("Job '3' not found")
    )
    client = TestClient(app)

    response = client.delete("/api/jobs/3")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "JOB_NOT_FOUND"


def test_cancel_job_already_completed_returns_409():
    app.dependency_overrides[get_job_service] = lambda: _FakeJobService(
        cancel_error=JobNotCancelableError("Job 3 is already completed")
    )
    client = TestClient(app)

    response = client.delete("/api/jobs/3")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "JOB_NOT_CANCELABLE"


def test_list_printer_jobs_filters_by_printer():
    other_job = {**_JOB_SUMMARY, "job_id": 4, "printer": "Other-Printer"}
    app.dependency_overrides[get_printer_service] = lambda: _FakePrinterService(exists=True)
    app.dependency_overrides[get_job_service] = lambda: _FakeJobService(jobs=[_JOB_SUMMARY, other_job])
    client = TestClient(app)

    response = client.get("/api/printers/Canon-G2030/jobs")

    assert response.status_code == 200
    assert response.json() == [_JOB_SUMMARY]


def test_list_printer_jobs_404_for_unknown_printer():
    app.dependency_overrides[get_printer_service] = lambda: _FakePrinterService(exists=False)
    app.dependency_overrides[get_job_service] = lambda: _FakeJobService(jobs=[_JOB_SUMMARY])
    client = TestClient(app)

    response = client.get("/api/printers/DoesNotExist/jobs")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PRINTER_NOT_FOUND"
