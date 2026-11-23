"""Search Repositories — GET /search/repositories.

These tests cover the repository search endpoint of the GitHub Search API.
The endpoint is read-only: no repository is created or deleted.

GitHub Search API rate limit for authenticated requests: 30 req/min.
Tests use a well-known public query (language:python) so the total_count
is stable and always greater than zero.
"""
import pytest

from config import settings
from config.settings import Endpoints
from core.assertions import assert_common, assert_error, assert_schema
from core.schemas import SEARCH_REPOSITORIES_SCHEMA


# ----------------------------------------------------------------- SEARCH_REPO_001: basic search with token
@pytest.mark.smoke
def test_tc_search_repo_001_verify_that_a_basic_repository_search_returns_200_with_token(github):
    response = github.get(Endpoints.SEARCH_REPOSITORIES, params={"q": "language:python", "per_page": 5})

    assert response.status_code == 200
    assert_common(response)
    body = response.json()
    assert_schema(body, SEARCH_REPOSITORIES_SCHEMA)
    assert body["total_count"] > 0
    assert isinstance(body["items"], list)
    assert len(body["items"]) > 0


# ----------------------------------------------------------------- SEARCH_REPO_002: per_page limits results
def test_tc_search_repo_002_verify_that_per_page_limits_the_number_of_items_returned(github):
    response = github.get(Endpoints.SEARCH_REPOSITORIES, params={"q": "language:python", "per_page": 3})

    assert response.status_code == 200
    assert_common(response)
    items = response.json()["items"]
    assert len(items) <= 3


# ----------------------------------------------------------------- SEARCH_REPO_003: each item has required fields
def test_tc_search_repo_003_verify_that_each_result_item_contains_the_required_fields(github):
    response = github.get(Endpoints.SEARCH_REPOSITORIES, params={"q": "language:python", "per_page": 5})

    assert response.status_code == 200
    assert_common(response)
    for item in response.json()["items"]:
        assert "id" in item
        assert "name" in item
        assert "full_name" in item
        assert "html_url" in item
        assert isinstance(item["private"], bool)


# ----------------------------------------------------------------- SEARCH_REPO_004: search without token returns 200
@pytest.mark.no_token
def test_tc_search_repo_004_verify_that_a_repository_search_without_a_token_returns_200(anonymous):
    response = anonymous.get(Endpoints.SEARCH_REPOSITORIES, params={"q": "language:python", "per_page": 1})

    assert response.status_code == 200
    assert_common(response)
    assert response.json()["total_count"] > 0


# ----------------------------------------------------------------- SEARCH_REPO_005: missing query param returns 422
@pytest.mark.negative
def test_tc_search_repo_005_verify_that_a_missing_query_parameter_returns_422(github):
    response = github.get(Endpoints.SEARCH_REPOSITORIES)

    assert response.status_code == 422
    assert_common(response)


# ----------------------------------------------------------------- SEARCH_REPO_006: sort by stars is accepted
def test_tc_search_repo_006_verify_that_sorting_by_stars_is_accepted(github):
    response = github.get(
        Endpoints.SEARCH_REPOSITORIES,
        params={"q": "language:python", "sort": "stars", "order": "desc", "per_page": 5},
    )

    assert response.status_code == 200
    assert_common(response)
    items = response.json()["items"]
    stars = [item["stargazers_count"] for item in items]
    assert stars == sorted(stars, reverse=True), "Items are not sorted by stars in descending order"


# ----------------------------------------------------------------- SEARCH_REPO_007: search for specific repo by name
def test_tc_search_repo_007_verify_that_searching_by_exact_name_returns_matching_results(github):
    # octocat/Hello-World is a well-known public repository that always exists.
    response = github.get(
        Endpoints.SEARCH_REPOSITORIES,
        params={"q": "repo:octocat/Hello-World", "per_page": 1},
    )

    assert response.status_code == 200
    assert_common(response)
    body = response.json()
    assert body["total_count"] >= 1
    names = [item["full_name"] for item in body["items"]]
    assert "octocat/Hello-World" in names


# ----------------------------------------------------------------- SEARCH_REPO_008: rate limit header is present
def test_tc_search_repo_008_verify_that_the_search_rate_limit_header_is_present_in_the_response(github):
    response = github.get(Endpoints.SEARCH_REPOSITORIES, params={"q": "language:python", "per_page": 1})

    assert response.status_code == 200
    assert_common(response)
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
