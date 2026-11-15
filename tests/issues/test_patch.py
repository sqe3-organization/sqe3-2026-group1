"""PATCH /repos/{owner}/{repo}/issues/{issue_number} (folder 02 of the Postman collection).

In Postman, PATCH_004 and PATCH_006 reused the issue left by PATCH_003.
Here every test gets its own issue from the open_issue fixture, so they are independent."""
from datetime import datetime

import pytest

from config import settings
from config.settings import Endpoints
from core import data_factory
from core.assertions import assert_common, assert_error, assert_schema
from core.schemas import ISSUE_SCHEMA


@pytest.mark.negative
def test_tc_iss_patch_005_verify_that_a_non_existent_issue_cannot_be_updated(github):
    response = github.patch(Endpoints.issue(settings.NON_EXISTENT_ISSUE), json={"title": "TC_ISS_PATCH_005"})
    assert_error(response, 404, "Not Found")


@pytest.mark.smoke
def test_tc_iss_patch_001_verify_that_an_issue_title_and_body_can_be_updated(github, open_issue):
    changes = {"title": data_factory.issue_title("TC_ISS_PATCH_001 updated"), "body": data_factory.issue_body()}
    response = github.patch(Endpoints.issue(open_issue["number"]), json=changes)

    assert response.status_code == 200
    assert_common(response)
    assert response.json()["title"] == changes["title"]
    assert response.json()["body"] == changes["body"]
    assert response.json()["number"] == open_issue["number"]
    assert_schema(response.json(), ISSUE_SCHEMA)
    # data integrity
    saved = github.get(Endpoints.issue(open_issue["number"])).json()
    assert saved["title"] == changes["title"]
    assert saved["body"] == changes["body"]
    assert saved["state"] == "open"


def test_tc_iss_patch_002_verify_that_an_issue_can_be_closed_as_completed(github, open_issue):
    response = github.patch(Endpoints.issue(open_issue["number"]), json={"state": "closed", "state_reason": "completed"})

    assert response.status_code == 200
    assert_common(response)
    issue = response.json()
    assert issue["state"] == "closed"
    assert issue["state_reason"] == "completed"
    assert issue["closed_at"] is not None
    datetime.fromisoformat(issue["closed_at"].replace("Z", "+00:00"))  # valid ISO 8601 date


def test_tc_iss_patch_003_verify_that_a_closed_issue_can_be_reopened(github, closed_issue):
    response = github.patch(Endpoints.issue(closed_issue["number"]), json={"state": "open"})

    assert response.status_code == 200
    assert_common(response)
    assert response.json()["state"] == "open"
    assert response.json()["state_reason"] == "reopened"
    assert response.json()["closed_at"] is None


@pytest.mark.negative
def test_tc_iss_patch_004_verify_that_an_issue_cannot_be_updated_with_an_invalid_token(github, invalid_client, open_issue):
    response = invalid_client.patch(Endpoints.issue(open_issue["number"]), json={"title": "TC_ISS_PATCH_004 - must not be applied"})

    assert_error(response, 401, "Bad credentials")
    # data integrity: nothing changed
    assert github.get(Endpoints.issue(open_issue["number"])).json()["title"] == open_issue["title"]


@pytest.mark.negative
def test_tc_iss_patch_006_verify_that_an_issue_cannot_be_updated_with_an_invalid_state(github, open_issue):
    response = github.patch(Endpoints.issue(open_issue["number"]), json={"state": "done"})

    # Known defect (Lab 1 and Lab 2): GitHub answers 200 and ignores the value instead of 422
    assert response.status_code == 422
    assert github.get(Endpoints.issue(open_issue["number"])).json()["state"] == "open"
