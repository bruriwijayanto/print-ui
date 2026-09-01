from app.services.job_service import map_job_state


def _attrs(job_state: int, reasons=None) -> dict:
    return {"job-state": job_state, "job-state-reasons": reasons or []}


def test_pending_state():
    assert map_job_state(_attrs(3)) == "PENDING"


def test_pending_held_state():
    assert map_job_state(_attrs(4)) == "PENDING"


def test_processing_state():
    assert map_job_state(_attrs(5)) == "PROCESSING"


def test_processing_stopped_state():
    assert map_job_state(_attrs(6)) == "PROCESSING"


def test_canceled_state():
    assert map_job_state(_attrs(7)) == "CANCELED"


def test_aborted_state_maps_to_failed():
    assert map_job_state(_attrs(8)) == "FAILED"


def test_completed_state():
    assert map_job_state(_attrs(9)) == "COMPLETED"


def test_processing_with_error_reason_becomes_failed():
    assert map_job_state(_attrs(5, ["media-empty-error"])) == "FAILED"


def test_pending_with_error_reason_becomes_failed():
    assert map_job_state(_attrs(3, ["printer-stopped-error"])) == "FAILED"


def test_completed_with_unrelated_reason_stays_completed():
    assert map_job_state(_attrs(9, ["job-completed-successfully"])) == "COMPLETED"


def test_unknown_state_value():
    assert map_job_state(_attrs(999)) == "UNKNOWN"


def test_reasons_as_single_string_not_list():
    assert map_job_state({"job-state": 5, "job-state-reasons": "media-empty-error"}) == "FAILED"
