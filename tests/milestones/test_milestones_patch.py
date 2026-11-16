"""PATCH /repos/{owner}/{repo}/milestones/{number} (Update a milestone)."""
import pytest

from config import settings
from config.settings import Endpoints
from core.assertions import assert_common, assert_error, assert_error_contains, assert_schema
from core.schemas import MILESTONE_SCHEMA

INVALID_STATE = "pending"


@pytest.mark.negative
def test_tc_milestone_patch_004_verify_that_a_nonexistent_milestone_cannot_be_updated(github):
    response = github.patch(Endpoints.milestone(settings.NON_EXISTENT_MILESTONE), json={"title": "qa-pm-ghost"})
    assert_error(response, 404, "Not Found")


@pytest.mark.smoke
def test_tc_milestone_patch_001_verify_that_an_existing_milestone_can_be_updated(github, existing_milestone):
    new_values = {
        "title": existing_milestone["title"] + "-updated",
        "description": "Updated description",
        "due_on": "2027-01-31T00:00:00Z",
    }
    response = github.patch(Endpoints.milestone(existing_milestone["number"]), json=new_values)

    assert response.status_code == 200
    assert_common(response)
    assert response.json()["title"] == new_values["title"]
    assert response.json()["description"] == new_values["description"]
    assert_schema(response.json(), MILESTONE_SCHEMA)


def test_tc_milestone_patch_002_verify_that_an_open_milestone_can_be_closed(github, existing_milestone):
    response = github.patch(Endpoints.milestone(existing_milestone["number"]), json={"state": "closed"})

    assert response.status_code == 200
    assert_common(response)
    assert response.json()["state"] == "closed"
    assert isinstance(response.json()["closed_at"], str)


def test_tc_milestone_patch_003_verify_that_milestone_changes_persist_after_updating(github, existing_milestone):
    new_description = "Persistence check"
    response = github.patch(Endpoints.milestone(existing_milestone["number"]), json={"description": new_description})

    assert response.status_code == 200
    assert_common(response)
    retrieved_milestone = github.get(Endpoints.milestone(existing_milestone["number"]))
    assert retrieved_milestone.status_code == 200
    assert retrieved_milestone.json()["description"] == new_description


@pytest.mark.negative
def test_tc_milestone_patch_005_verify_that_a_milestone_cannot_be_updated_with_an_invalid_state(github, existing_milestone):
    response = github.patch(Endpoints.milestone(existing_milestone["number"]), json={"state": INVALID_STATE})

    assert_error_contains(response, 422, "state")
    milestone_after_rejected_update = github.get(Endpoints.milestone(existing_milestone["number"]))
    assert milestone_after_rejected_update.json()["state"] == "open"