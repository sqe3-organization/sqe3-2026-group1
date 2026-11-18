"""GET /repos/{owner}/{repo} (folder 02_GET_Read_Repo of the Postman collection): the cases that need no repository to be created.

They read the private repository of OWNER named in READ_REPO (readRepo in Postman), so nothing is created."""
import pytest

from config import settings
from config.settings import Endpoints
from core.assertions import assert_common, assert_error, assert_schema
from core.schemas import REPO_SCHEMA


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


@pytest.mark.negative
@pytest.mark.no_token
def test_tc_repo_get_003_verify_that_a_private_repo_without_a_token_returns_404(anonymous, read_repo_path):
    response = anonymous.get(read_repo_path)

    assert_error(response, 404, "Not Found")


@pytest.mark.negative
def test_tc_repo_get_004_verify_that_a_non_existent_repo_returns_404(github):
    response = github.get(Endpoints.repository(settings.NON_EXISTENT_REPO))

    assert_error(response, 404, "Not Found")


def test_tc_repo_get_005_verify_that_the_rate_limit_with_a_token_is_5000(github, read_repo_path):
    response = github.get(read_repo_path)

    assert response.status_code == 200
    assert_common(response)
    assert response.headers["X-RateLimit-Limit"] == "5000"


@pytest.mark.negative
@pytest.mark.no_token
def test_tc_repo_get_006_verify_that_the_rate_limit_without_a_token_is_60(anonymous, read_repo_path):
    response = anonymous.get(read_repo_path)

    assert response.status_code == 404  # a private repository is not visible without a token
    assert_common(response)
    assert response.headers["X-RateLimit-Limit"] == "60"


def test_tc_repo_get_007_verify_that_the_repo_name_in_the_url_is_case_insensitive(github, read_repo_path):
    response = github.get(Endpoints.repository(settings.READ_REPO.lower()))

    assert response.status_code == 200
    assert_common(response)
    # full_name keeps the original casing of the repository name
    assert response.json()["full_name"] == f"{settings.OWNER}/{settings.READ_REPO}"
