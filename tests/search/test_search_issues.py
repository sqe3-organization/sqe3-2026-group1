"""Search Issues and Pull Requests — GET /search/issues.

These tests cover the issue search endpoint of the GitHub Search API.
The endpoint is read-only: no issue is created or deleted.

GitHub represents pull requests as issues in the Search API, so the
endpoint returns both. Tests use the public octocat/Hello-World repository
to have stable, predictable results without touching our own test data.
"""
import pytest

from config.settings import Endpoints
from core.assertions import assert_common, assert_error, assert_schema
from core.schemas import SEARCH_ISSUES_SCHEMA


# ----------------------------------------------------------------- SEARCH_ISS_001: basic issue search with token
@pytest.mark.smoke
def test_tc_search_iss_001_verify_that_a_basic_issue_search_returns_200_with_token(github):
    response = github.get(Endpoints.SEARCH_ISSUES, params={"q": "repo:octocat/Hello-World", "per_page": 5})

    assert response.status_code == 200
    assert_common(response)
    body = response.json()
    assert_schema(body, SEARCH_ISSUES_SCHEMA)
    assert isinstance(body["total_count"], int)
    assert isinstance(body["items"], list)


# ----------------------------------------------------------------- SEARCH_ISS_002: each item has required fields
def test_tc_search_iss_002_verify_that_each_result_item_contains_the_required_fields(github):
    response = github.get(Endpoints.SEARCH_ISSUES, params={"q": "repo:octocat/Hello-World", "per_page": 5})

    assert response.status_code == 200
    assert_common(response)
    for item in response.json()["items"]:
        assert "id" in item
        assert "number" in item
        assert "title" in item
        assert item["state"] in ("open", "closed")
        assert "html_url" in item


# ----------------------------------------------------------------- SEARCH_ISS_003: filter by state open
def test_tc_search_iss_003_verify_that_filtering_by_state_open_returns_only_open_issues(github):
    response = github.get(
        Endpoints.SEARCH_ISSUES,
        params={"q": "repo:octocat/Hello-World is:issue is:open", "per_page": 5},
    )

    assert response.status_code == 200
    assert_common(response)
    for item in response.json()["items"]:
        # The search qualifier is:open filters for open items; every returned item must be open.
        assert item["state"] == "open", f"Expected open, got {item['state']} for issue #{item['number']}"


# ----------------------------------------------------------------- SEARCH_ISS_004: missing query param returns 422
@pytest.mark.negative
def test_tc_search_iss_004_verify_that_a_missing_query_parameter_returns_422(github):
    response = github.get(Endpoints.SEARCH_ISSUES)

    assert response.status_code == 422
    assert_common(response)


# ----------------------------------------------------------------- SEARCH_ISS_005: search without token returns 200
@pytest.mark.no_token
def test_tc_search_iss_005_verify_that_an_issue_search_without_a_token_returns_200(anonymous):
    response = anonymous.get(
        Endpoints.SEARCH_ISSUES,
        params={"q": "repo:octocat/Hello-World", "per_page": 1},
    )

    assert response.status_code == 200
    assert_common(response)
