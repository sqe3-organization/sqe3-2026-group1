"""POST /repos/{owner}/{repo}/issues (folder 01 of the Postman collection)."""
import pytest

from config import settings
from config.settings import Endpoints
from core import data_factory
from core.assertions import assert_common, assert_error, assert_schema
from core.schemas import ISSUE_SCHEMA


# ----------------------------------------------------------------- [No preconditions] negative tests
@pytest.mark.negative
@pytest.mark.no_token
def test_tc_iss_post_003_verify_that_an_issue_cannot_be_created_without_a_token(anonymous):
    response = anonymous.post(Endpoints.ISSUES, json={"title": "TC_ISS_POST_003 - should not be created"})
    assert_error(response, 401, "Requires authentication")


@pytest.mark.negative
@pytest.mark.no_token
def test_tc_iss_post_004_verify_that_an_issue_cannot_be_created_with_an_invalid_token(invalid_client):
    response = invalid_client.post(Endpoints.ISSUES, json={"title": "TC_ISS_POST_004 - should not be created"})
    assert_error(response, 401, "Bad credentials")


@pytest.mark.negative
def test_tc_iss_post_005_verify_that_an_issue_cannot_be_created_without_a_title(github):
    response = github.post(Endpoints.ISSUES, json={"body": "Issue without title"})
    assert_error(response, 422, "title")


@pytest.mark.negative
def test_tc_iss_post_006_verify_that_an_issue_cannot_be_created_in_a_non_existent_repository(github):
    response = github.post(f"/repos/{settings.OWNER}/repo-that-does-not-exist-xyz/issues", json={"title": "TC_ISS_POST_006"})
    assert_error(response, 404, "Not Found")


# ----------------------------------------------------------------- [Cleanup] the test creates, the fixture closes
@pytest.mark.smoke
def test_tc_iss_post_001_verify_that_a_new_issue_can_be_created_with_only_a_title(github, created_issues):
    title = data_factory.issue_title("TC_ISS_POST_001")
    response = github.post(Endpoints.ISSUES, json={"title": title})

    # status code
    assert response.status_code == 201
    issue = response.json()
    assert "number" in issue
    created_issues.append(issue["number"])
    # headers
    assert_common(response)
    assert f"/issues/{issue['number']}" in response.headers["Location"]
    # body
    assert issue["state"] == "open"
    assert issue["title"] == title
    assert issue["number"] > 0
    # parameter types
    assert_schema(issue, ISSUE_SCHEMA)
    # data integrity
    saved = github.get(Endpoints.issue(issue["number"]))
    assert saved.status_code == 200
    assert saved.json()["title"] == title
    assert saved.json()["body"] is None
    assert saved.json()["labels"] == []
    assert saved.json()["locked"] is False


def test_tc_iss_post_002_verify_that_an_issue_can_be_created_with_title_body_labels_and_assignees(github, created_issues):
    payload = {
        "title": data_factory.issue_title("TC_ISS_POST_002"),
        "body": data_factory.issue_body(),
        "labels": ["bug"],
        "assignees": [settings.OWNER],
    }
    response = github.post(Endpoints.ISSUES, json=payload)

    assert response.status_code == 201
    issue = response.json()
    created_issues.append(issue["number"])
    assert_common(response)
    assert issue["body"] == payload["body"]
    assert "bug" in [label["name"] for label in issue["labels"]]
    assert settings.OWNER in [user["login"] for user in issue["assignees"]]
    assert_schema(issue, ISSUE_SCHEMA)
    # data integrity
    saved = github.get(Endpoints.issue(issue["number"])).json()
    assert saved["body"] == payload["body"]
    assert [label["name"] for label in saved["labels"]] == ["bug"]


@pytest.mark.boundary
def test_tc_iss_post_007_verify_that_an_issue_can_be_created_with_a_1_character_title(github, created_issues):
    response = github.post(Endpoints.ISSUES, json={"title": "A"})

    assert response.status_code == 201
    created_issues.append(response.json()["number"])
    assert_common(response)
    assert len(response.json()["title"]) == 1
    assert_schema(response.json(), ISSUE_SCHEMA)


@pytest.mark.boundary
@pytest.mark.negative
def test_tc_iss_post_008_verify_that_an_issue_cannot_be_created_with_a_body_over_65536_characters(github, created_issues):
    response = github.post(Endpoints.ISSUES, json={"title": "TC_ISS_POST_008 - long body", "body": data_factory.long_text(65537)})

    if response.status_code == 201:  # if GitHub ever accepts it, the issue is still cleaned up
        created_issues.append(response.json()["number"])
    assert_error(response, 422, "Validation Failed")
