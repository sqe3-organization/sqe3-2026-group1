"""POST /repos/{owner}/{repo}/milestones (Create a milestone)."""
import pytest

from config.settings import Endpoints
from core import data_factory
from core.assertions import assert_common, assert_error, assert_error_contains, assert_schema
from core.schemas import MILESTONE_SCHEMA

INVALID_STATE = "pending"
INVALID_DUE_DATE = "not-a-date"


def clean_up_milestone_if_wrongly_created(response, milestone_numbers_to_clean_up):
    if response.status_code == 201:
        milestone_numbers_to_clean_up.append(response.json()["number"])


@pytest.mark.negative
def test_tc_milestone_post_002_verify_that_a_milestone_cannot_be_created_without_a_title(github, milestone_numbers_to_clean_up):
    response = github.post(Endpoints.MILESTONES, json={"description": "No title"})

    clean_up_milestone_if_wrongly_created(response, milestone_numbers_to_clean_up)
    assert_error_contains(response, 422, "title")


@pytest.mark.negative
@pytest.mark.boundary
def test_tc_milestone_post_003_verify_that_a_milestone_cannot_be_created_with_an_empty_title(github, milestone_numbers_to_clean_up):
    response = github.post(Endpoints.MILESTONES, json={"title": ""})

    clean_up_milestone_if_wrongly_created(response, milestone_numbers_to_clean_up)
    assert_error_contains(response, 422, "title")


@pytest.mark.negative
def test_tc_milestone_post_005_verify_that_a_milestone_cannot_be_created_with_an_invalid_state(github, milestone_numbers_to_clean_up):
    milestone_with_invalid_state = {"title": data_factory.milestone_title("tc_milestone_post_005"), "state": INVALID_STATE}
    response = github.post(Endpoints.MILESTONES, json=milestone_with_invalid_state)

    clean_up_milestone_if_wrongly_created(response, milestone_numbers_to_clean_up)
    assert_error(response, 422, f"{INVALID_STATE} is not a member of")


@pytest.mark.negative
def test_tc_milestone_post_006_verify_that_a_milestone_cannot_be_created_with_an_invalid_due_date(github, milestone_numbers_to_clean_up):
    milestone_with_invalid_due_date = {"title": data_factory.milestone_title("tc_milestone_post_006"), "due_on": INVALID_DUE_DATE}
    response = github.post(Endpoints.MILESTONES, json=milestone_with_invalid_due_date)

    clean_up_milestone_if_wrongly_created(response, milestone_numbers_to_clean_up)
    assert_error(response, 422, f"{INVALID_DUE_DATE} is not a valid date-time")


@pytest.mark.negative
def test_tc_milestone_post_007_verify_that_a_milestone_cannot_be_created_with_a_null_due_date(github, milestone_numbers_to_clean_up):
    milestone_with_null_due_date = {"title": data_factory.milestone_title("tc_milestone_post_007"), "due_on": None}
    response = github.post(Endpoints.MILESTONES, json=milestone_with_null_due_date)

    clean_up_milestone_if_wrongly_created(response, milestone_numbers_to_clean_up)
    assert_error_contains(response, 422, "due_on")


@pytest.mark.smoke
def test_tc_milestone_post_001_verify_that_a_milestone_can_be_created_with_valid_data(github, milestone_numbers_to_clean_up):
    new_milestone = {
        "title": data_factory.milestone_title("tc_milestone_post_001"),
        "description": "Milestone created by a pytest test",
        "state": "open",
        "due_on": "2026-12-31T00:00:00Z",
    }
    response = github.post(Endpoints.MILESTONES, json=new_milestone)

    assert response.status_code == 201
    created_milestone = response.json()
    milestone_numbers_to_clean_up.append(created_milestone["number"])
    assert_common(response)
    assert created_milestone["title"] == new_milestone["title"]
    assert created_milestone["description"] == new_milestone["description"]
    assert created_milestone["state"] == "open"
    assert created_milestone["number"] > 0
    assert created_milestone["due_on"] is not None
    assert_schema(created_milestone, MILESTONE_SCHEMA)
    retrieved_milestone = github.get(Endpoints.milestone(created_milestone["number"]))
    assert retrieved_milestone.status_code == 200
    assert retrieved_milestone.json()["title"] == new_milestone["title"]


@pytest.mark.negative
def test_tc_milestone_post_004_verify_that_a_milestone_cannot_be_created_with_an_existing_title(github, existing_milestone, milestone_numbers_to_clean_up):
    response = github.post(Endpoints.MILESTONES, json={"title": existing_milestone["title"]})

    clean_up_milestone_if_wrongly_created(response, milestone_numbers_to_clean_up)
    assert_error_contains(response, 422, "title")
    reports_title_already_exists = any(
        error["code"] == "already_exists" and error["field"] == "title" for error in response.json()["errors"]
    )
    assert reports_title_already_exists