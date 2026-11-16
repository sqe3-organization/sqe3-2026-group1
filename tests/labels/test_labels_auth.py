"""Authentication and permission tests of POST /repos/{owner}/{repo}/labels.

Added after the feedback of Group 2 (they are not in the Lab 1 table).
"""
import pytest

from config.settings import Endpoints
from core import data_factory
from core.assertions import assert_common, assert_error, assert_schema
from core.label_assertions import assert_label_does_not_exist
from core.schemas import ERROR_SCHEMA

FORBIDDEN_OR_HIDDEN_STATUS_CODES = (403, 404)


def label_that_must_not_be_created(test_case_id, description):
    return {"name": data_factory.label_name(test_case_id), "color": "1D76DB", "description": description}


@pytest.mark.negative
@pytest.mark.no_token
def test_tc_label_auth_001_verify_that_a_label_cannot_be_created_without_a_token(anonymous):
    label = label_that_must_not_be_created("tc_label_auth_001", "Must not be created without a token")
    response = anonymous.post(Endpoints.LABELS, json=label)

    assert_error(response, 401, "Requires authentication")
    assert_label_does_not_exist(anonymous, label["name"])


@pytest.mark.negative
@pytest.mark.no_token
def test_tc_label_auth_002_verify_that_a_label_cannot_be_created_with_an_invalid_token(invalid_client, anonymous):
    label = label_that_must_not_be_created("tc_label_auth_002", "Must not be created with an invalid token")
    response = invalid_client.post(Endpoints.LABELS, json=label)

    assert_error(response, 401, "Bad credentials")
    assert_label_does_not_exist(anonymous, label["name"])


@pytest.mark.negative
def test_tc_label_perm_001_verify_that_a_label_cannot_be_created_in_a_repository_without_write_permission(github, anonymous):
    label = label_that_must_not_be_created("tc_label_perm_001", "Must not be created without permission")
    response = github.post(Endpoints.PUBLIC_LABELS, json=label)

    assert response.status_code in FORBIDDEN_OR_HIDDEN_STATUS_CODES
    assert response.json()["message"]
    assert_schema(response.json(), ERROR_SCHEMA)
    assert_common(response)
    assert_label_does_not_exist(anonymous, label["name"], labels_path=Endpoints.PUBLIC_LABELS)