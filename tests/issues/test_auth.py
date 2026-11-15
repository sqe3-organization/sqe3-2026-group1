"""Setup & Authorization (folder 00 of the Postman collection)."""
import pytest

from config import settings
from config.settings import Endpoints
from core.assertions import assert_common


@pytest.mark.smoke
def test_tc_iss_auth_001_verify_that_the_token_authenticates_the_expected_user(github):
    response = github.get(Endpoints.USER)

    assert response.status_code == 200
    assert_common(response)
    assert response.headers["X-RateLimit-Limit"] == "5000"
    assert response.json()["login"] == settings.OWNER
    assert isinstance(response.json()["id"], int)


@pytest.mark.no_token
def test_tc_iss_auth_002_verify_that_a_public_request_without_token_works_with_the_anonymous_limit(anonymous):
    response = anonymous.get(Endpoints.PUBLIC_REPOSITORY)

    assert response.status_code == 200
    assert_common(response)
    assert response.headers["X-RateLimit-Limit"] == "60"
    assert response.json()["full_name"] == f"{settings.PUBLIC_OWNER}/{settings.PUBLIC_REPO}"
    assert response.json()["private"] is False
