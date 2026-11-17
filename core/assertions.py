"""Reusable checks. In Postman the common ones lived in the collection Tests tab."""
import json

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

def assert_error_contains(response, status, text):
    """Error responses whose message does not name the field (for example 422 on labels and milestones):
    status, the text anywhere in the error body, error schema and common checks."""
    assert response.status_code == status, f"expected {status}, got {response.status_code}"
    assert text in json.dumps(response.json()), f"'{text}' not found in {response.json()}"
    assert_schema(response.json(), ERROR_SCHEMA)
    assert_common(response)


NO_CONTENT_STATUS_CODE = 204
NEXT_PAGE_LINK = "next"
LAST_PAGE_LINK = "last"


def assert_no_content(response):
    assert response.status_code == NO_CONTENT_STATUS_CODE
    assert_common(response)
    assert response.text == ""


def assert_has_more_pages(response):
    assert NEXT_PAGE_LINK in response.links
    assert LAST_PAGE_LINK in response.links


def assert_is_single_page(response):
    assert NEXT_PAGE_LINK not in response.links
