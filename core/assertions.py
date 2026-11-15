"""Reusable checks. In Postman the common ones lived in the collection Tests tab."""
from jsonschema import validate

from config import settings
from core.schemas import ERROR_SCHEMA


def assert_common(response):
    """Checks every response must pass: response time, Content-Type and request id header."""
    elapsed_ms = response.elapsed.total_seconds() * 1000
    assert elapsed_ms < settings.MAX_RESPONSE_TIME_MS, f"response took {elapsed_ms:.0f} ms"
    if response.status_code != 204:
        assert "application/json" in response.headers["Content-Type"]
    assert "X-GitHub-Request-Id" in response.headers


def assert_schema(body, schema):
    """Parameter types: raises jsonschema.ValidationError with the exact field if it fails."""
    validate(instance=body, schema=schema)


def assert_error(response, status, message):
    """Error responses: status, message and error schema in one call."""
    assert response.status_code == status
    assert message in response.json()["message"]
    assert_schema(response.json(), ERROR_SCHEMA)
    assert_common(response)
