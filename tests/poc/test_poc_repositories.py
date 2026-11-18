"""Proofs of concept for the Repositories module.

The general features of requests and pytest are already proved in test_poc_requests.py and
test_poc_pytest.py. These tests check what is specific to Repositories before migrating the
29 test cases. None of them needs a token and none of them creates a repository, so they do not
count against GitHub's limits on content creation.
"""
from config import settings
from config.settings import Endpoints
from core.assertions import assert_common, assert_error, assert_schema
from core.schemas import REPO_SCHEMA


def test_public_repository_can_be_read_without_a_token_and_matches_the_repository_schema(anonymous):
    """Postman TC_REPO_GET_002: a public repository answers 200 to a client with no Authorization header."""
    response = anonymous.get(Endpoints.PUBLIC_REPOSITORY)

    assert response.status_code == 200
    assert_common(response)
    assert response.json()["private"] is False
    assert_schema(response.json(), REPO_SCHEMA)


def test_requests_does_not_raise_on_a_404_and_the_error_has_the_error_schema(anonymous):
    """Postman TC_REPO_GET_004: a repository that does not exist is a normal response, not an exception."""
    response = anonymous.get(f"/repos/{settings.PUBLIC_OWNER}/{settings.NON_EXISTENT_REPO}")

    assert_error(response, 404, "Not Found")


def test_repository_name_in_the_url_is_case_insensitive_and_full_name_keeps_the_original_casing(anonymous):
    """Postman TC_REPO_GET_007: the URL is built with the name in lowercase."""
    lowercase_path = f"/repos/{settings.PUBLIC_OWNER}/{settings.PUBLIC_REPO.lower()}"
    response = anonymous.get(lowercase_path)

    assert response.status_code == 200
    assert_common(response)
    assert response.json()["full_name"] == f"{settings.PUBLIC_OWNER}/{settings.PUBLIC_REPO}"


def test_unauthenticated_requests_report_a_rate_limit_of_60(anonymous):
    """Postman TC_REPO_GET_006: headers are read from response.headers, which is case-insensitive."""
    response = anonymous.get(Endpoints.PUBLIC_REPOSITORY)

    assert response.headers["X-RateLimit-Limit"] == "60"
    assert response.headers["x-ratelimit-limit"] == "60"
