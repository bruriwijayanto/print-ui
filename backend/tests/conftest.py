import pytest

from app.dependencies import get_current_api_key
from app.main import app


@pytest.fixture(autouse=True)
def bypass_api_key_auth():
    """Most tests exercise route/service logic, not authentication itself —
    test_auth.py explicitly removes this override to test the real thing."""
    app.dependency_overrides[get_current_api_key] = lambda: "test-key"
    yield
    app.dependency_overrides.pop(get_current_api_key, None)
