"""GET /repos/{owner}/{repo} (folder 02_GET_Read_Repo of the Postman collection).

GET_001, GET_003 through GET_007 read the private repository named in READ_REPO (readRepo in Postman).
No repository is created by those tests.

GET_002 reads a public repository without authentication. It uses the session-scoped shared_public_repo
fixture so no extra repository is created for this test alone.
"""
import pytest

from config import settings
from config.settings import Endpoints
from core.assertions import assert_common, assert_error, assert_schema
from core.schemas import REPO_SCHEMA


# ----------------------------------------------------------------- GET_001: private repo with valid token
@pytest.mark.smoke
def test_tc_repo_get_001_verify_that_a_private_repo_is_returned_with_a_valid_token(github, read_repo_path):
    response = github.get(read_repo_path)

    assert response.status_code == 200
    assert_common(response)
    repo = response.json()
    assert repo["private"] is True
    assert repo["visibility"] == "private"
    assert repo["permissions"]["admin"] is True
    assert_schema(repo, REPO_SCHEMA)


# ----------------------------------------------------------------- GET_002: public repo without token
def test_tc_repo_get_002_verify_that_a_public_repo_is_accessible_without_a_token(anonymous, shared_public_repo):
    # shared_public_repo is a session-scoped public repository created by the fixture.
    # This test verifies it is reachable via GET without an Authorization header.
    response = anonymous.get(Endpoints.repository(shared_public_repo))

    assert response.status_code == 200
    assert_common(response)
    repo = response.json()
    assert repo["private"] is False
    assert repo["name"] == shared_public_repo


# ----------------------------------------------------------------- GET_003: private repo without token returns 404
@pytest.mark.negative
@pytest.mark.no_token
def test_tc_repo_get_003_verify_that_a_private_repo_without_a_token_returns_404(anonymous, read_repo_path):
    response = anonymous.get(read_repo_path)

    assert_error(response, 404, "Not Found")


# ----------------------------------------------------------------- GET_004: non-existent repo returns 404
@pytest.mark.negative
def test_tc_repo_get_004_verify_that_a_non_existent_repo_returns_404(github):
    response = github.get(Endpoints.repository(settings.NON_EXISTENT_REPO))

    assert_error(response, 404, "Not Found")


# ----------------------------------------------------------------- GET_005: rate limit is 5000 with token
def test_tc_repo_get_005_verify_that_the_rate_limit_with_a_token_is_5000(github, read_repo_path):
    response = github.get(read_repo_path)

    assert response.status_code == 200
    assert_common(response)
    assert response.headers["X-RateLimit-Limit"] == "5000"


# ----------------------------------------------------------------- GET_006: rate limit is 60 without token
@pytest.mark.negative
@pytest.mark.no_token
def test_tc_repo_get_006_verify_that_the_rate_limit_without_a_token_is_60(anonymous, read_repo_path):
    response = anonymous.get(read_repo_path)

    assert response.status_code == 404  # a private repository is not visible without a token
    assert_common(response)
    assert response.headers["X-RateLimit-Limit"] == "60"


# ----------------------------------------------------------------- GET_007: URL is case-insensitive
def test_tc_repo_get_007_verify_that_the_repo_name_in_the_url_is_case_insensitive(github, read_repo_path):
    response = github.get(Endpoints.repository(settings.READ_REPO.lower()))

    assert response.status_code == 200
    assert_common(response)
    # full_name keeps the original casing of the repository name
    assert response.json()["full_name"] == f"{settings.OWNER}/{settings.READ_REPO}"
