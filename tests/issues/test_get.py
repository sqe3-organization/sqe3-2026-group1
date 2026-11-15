"""GET issues (folder 03 of the Postman collection)."""
import pytest

from config import settings
from config.settings import Endpoints
from core.assertions import assert_common, assert_error, assert_schema
from core.issue_helpers import cleanup_issues, create_issue, wait_until
from core.schemas import ISSUE_SCHEMA


# ----------------------------------------------------------------- [No preconditions]
@pytest.mark.no_token
def test_tc_iss_get_004_verify_that_the_issues_list_also_returns_pull_requests(anonymous):
    response = anonymous.get(Endpoints.PUBLIC_ISSUES, params={"per_page": 10, "state": "all"})

    assert response.status_code == 200
    assert_common(response)
    assert isinstance(response.json(), list)
    assert any("pull_request" in item for item in response.json())


@pytest.mark.negative
def test_tc_iss_get_005_verify_that_a_non_existent_issue_cannot_be_retrieved(github):
    response = github.get(Endpoints.issue(settings.NON_EXISTENT_ISSUE))
    assert_error(response, 404, "Not Found")


@pytest.mark.negative
def test_tc_iss_get_006_verify_that_an_invalid_state_filter_is_rejected(github):
    response = github.get(Endpoints.ISSUES, params={"state": "foo"})

    assert_error(response, 422, "Validation Failed")
    assert response.json()["errors"][0]["field"] == "state"


@pytest.mark.boundary
@pytest.mark.no_token
def test_tc_iss_get_007_verify_the_maximum_page_size_per_page_100(anonymous):
    response = anonymous.get(Endpoints.PUBLIC_ISSUES, params={"per_page": 100, "state": "all"})

    assert response.status_code == 200
    assert_common(response)
    assert len(response.json()) == 100
    assert 'rel="next"' in response.headers["Link"]


@pytest.mark.boundary
@pytest.mark.no_token
def test_tc_iss_get_008_verify_that_per_page_above_the_maximum_is_capped_at_100(anonymous):
    response = anonymous.get(Endpoints.PUBLIC_ISSUES, params={"per_page": 101, "state": "all"})

    assert response.status_code == 200
    assert_common(response)
    assert len(response.json()) <= 100


# ----------------------------------------------------------------- [Pre and Cleanup] read-only tests share data
@pytest.fixture(scope="module")
def repo_issues(github):
    """Module scope: created once for the three read-only tests, closed at the end of the file."""
    data = {
        "open": create_issue(github, "TC_ISS_GET setup"),
        "bug": create_issue(github, "TC_ISS_GET_003 setup", labels=["bug"]),
    }
    yield data
    cleanup_issues(github, [data["open"]["number"], data["bug"]["number"]])


@pytest.mark.smoke
def test_tc_iss_get_001_verify_that_the_list_of_open_issues_can_be_retrieved(github, repo_issues):
    def list_contains_issue():
        res = github.get(Endpoints.ISSUES, params={"state": "open", "per_page": 100})
        return res if repo_issues["open"]["number"] in [i["number"] for i in res.json()] else None

    response = wait_until(list_contains_issue)

    assert response, "the new issue never appeared in the open list"
    assert response.status_code == 200
    assert_common(response)
    assert len(response.json()) > 0
    assert all(issue["state"] == "open" for issue in response.json())


def test_tc_iss_get_002_verify_that_a_single_issue_can_be_retrieved_by_its_number(github, repo_issues):
    expected = repo_issues["open"]
    response = github.get(Endpoints.issue(expected["number"]))

    assert response.status_code == 200
    assert_common(response)
    assert response.json()["number"] == expected["number"]
    assert response.json()["title"] == expected["title"]
    assert_schema(response.json(), ISSUE_SCHEMA)


def test_tc_iss_get_003_verify_that_issues_can_be_filtered_by_label(github, repo_issues):
    def list_contains_bug_issue():
        res = github.get(Endpoints.ISSUES, params={"labels": "bug", "state": "all"})
        return res if repo_issues["bug"]["number"] in [i["number"] for i in res.json()] else None

    response = wait_until(list_contains_bug_issue)

    assert response, "the issue with label bug never appeared in the filtered list"
    assert response.status_code == 200
    assert_common(response)
    assert all("bug" in [label["name"] for label in issue["labels"]] for issue in response.json())
