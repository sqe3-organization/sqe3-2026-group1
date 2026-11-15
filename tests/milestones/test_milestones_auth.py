"""Authentication and permission tests of POST /repos/{owner}/{repo}/milestones.

Added after the feedback of Group 2 (they are not in the Lab 1 table).
"""
import pytest

from config.settings import Endpoints
from core import data_factory
from core.assertions import assert_common, assert_error, assert_schema
from core.schemas import ERROR_SCHEMA

FORBIDDEN_OR_HIDDEN_STATUS_CODES = (403, 404)


def milestone_that_must_not_be_created(test_case_id, description):
    return {"title": data_factory.milestone_title(test_case_id), "description": description}


def assert_milestone_was_not_created(client, milestones_path, title):
    response = client.get(milestones_path, params={"state": "all", "per_page": 100})
    assert response.status_code == 200
    assert title not in [milestone["title"] for milestone in response.json()]


@pytest.mark.negative
@pytest.mark.no_token
def test_tc_milestone_auth_001_verify_that_a_milestone_cannot_be_created_without_a_token(anonymous):
    milestone = milestone_that_must_not_be_created("tc_milestone_auth_001", "Must not be created without a token")
    response = anonymous.post(Endpoints.MILESTONES, json=milestone)

    assert_error(response, 401, "Requires authentication")
    assert_milestone_was_not_created(anonymous, Endpoints.MILESTONES, milestone["title"])


@pytest.mark.negative
@pytest.mark.no_token
def test_tc_milestone_auth_002_verify_that_a_milestone_cannot_be_created_with_an_invalid_token(invalid_client, anonymous):
    milestone = milestone_that_must_not_be_created("tc_milestone_auth_002", "Must not be created with an invalid token")
    response = invalid_client.post(Endpoints.MILESTONES, json=milestone)

    assert_error(response, 401, "Bad credentials")
    assert_milestone_was_not_created(anonymous, Endpoints.MILESTONES, milestone["title"])


@pytest.mark.negative
def test_tc_milestone_perm_001_verify_that_a_milestone_cannot_be_created_in_a_repository_without_write_permission(github, anonymous):
    milestone = milestone_that_must_not_be_created("tc_milestone_perm_001", "Must not be created without permission")
    response = github.post(Endpoints.PUBLIC_MILESTONES, json=milestone)

    assert response.status_code in FORBIDDEN_OR_HIDDEN_STATUS_CODES
    assert response.json()["message"]
    assert_schema(response.json(), ERROR_SCHEMA)
    assert_common(response)
    assert_milestone_was_not_created(anonymous, Endpoints.PUBLIC_MILESTONES, milestone["title"])