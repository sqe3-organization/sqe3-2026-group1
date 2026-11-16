"""POST /repos/{owner}/{repo}/labels (Create a label)."""
import pytest

from config.settings import Endpoints
from core import data_factory
from core.assertions import assert_common, assert_error_contains, assert_schema
from core.label_assertions import assert_label_can_be_retrieved, assert_label_matches
from core.schemas import LABEL_SCHEMA

VALID_COLOR = "1D76DB"
INVALID_COLOR = "ZZZZZZ"
MAX_DESCRIPTION_LENGTH = 100


def clean_up_label_if_wrongly_created(response, label_names_to_clean_up):
    if response.status_code == 201:
        label_names_to_clean_up.append(response.json()["name"])


@pytest.mark.negative
def test_tc_label_post_003_verify_that_a_label_cannot_be_created_with_an_invalid_color(github, label_names_to_clean_up):
    label_with_invalid_color = {
        "name": data_factory.label_name("tc_label_post_003"),
        "color": INVALID_COLOR,
        "description": "Invalid color",
    }
    response = github.post(Endpoints.LABELS, json=label_with_invalid_color)

    clean_up_label_if_wrongly_created(response, label_names_to_clean_up)
    assert_error_contains(response, 422, "color")


@pytest.mark.negative
@pytest.mark.boundary
def test_tc_label_post_005_verify_that_a_label_cannot_be_created_with_a_description_over_100_characters(github, label_names_to_clean_up):
    label_with_too_long_description = {
        "name": data_factory.label_name("tc_label_post_005"),
        "color": VALID_COLOR,
        "description": data_factory.description(MAX_DESCRIPTION_LENGTH + 1),
    }
    response = github.post(Endpoints.LABELS, json=label_with_too_long_description)

    clean_up_label_if_wrongly_created(response, label_names_to_clean_up)
    assert_error_contains(response, 422, "description")


@pytest.mark.smoke
def test_tc_label_post_001_verify_that_a_label_can_be_created_with_valid_fields(github, label_names_to_clean_up):
    new_label = {
        "name": data_factory.label_name("tc_label_post_001"),
        "color": VALID_COLOR,
        "description": "Temporary label for API testing",
    }
    response = github.post(Endpoints.LABELS, json=new_label)

    assert response.status_code == 201
    created_label = response.json()
    label_names_to_clean_up.append(created_label["name"])
    assert_common(response)
    assert_label_matches(created_label, new_label)
    assert created_label["default"] is False
    assert_schema(created_label, LABEL_SCHEMA)
    assert_label_can_be_retrieved(github, new_label["name"])


@pytest.mark.negative
def test_tc_label_post_002_verify_that_a_label_cannot_be_created_without_the_required_color(github, label_names_to_clean_up):
    # Known API defect: GitHub accepts a label without color (201) and assigns "ededed", so this test
    # fails on purpose. The Lab 1 expectation is kept because the endpoint documentation contradicts itself.
    label_without_color = {
        "name": data_factory.label_name("tc_label_post_002"),
        "description": "Label without color",
    }
    response = github.post(Endpoints.LABELS, json=label_without_color)

    clean_up_label_if_wrongly_created(response, label_names_to_clean_up)
    assert_error_contains(response, 422, "color")


@pytest.mark.boundary
def test_tc_label_post_004_verify_that_a_label_can_be_created_with_a_100_character_description(github, label_names_to_clean_up):
    label_with_longest_description = {
        "name": data_factory.label_name("tc_label_post_004"),
        "color": VALID_COLOR,
        "description": data_factory.description(MAX_DESCRIPTION_LENGTH),
    }
    response = github.post(Endpoints.LABELS, json=label_with_longest_description)

    assert response.status_code == 201
    created_label = response.json()
    label_names_to_clean_up.append(created_label["name"])
    assert_common(response)
    assert len(created_label["description"]) == MAX_DESCRIPTION_LENGTH
    assert_schema(created_label, LABEL_SCHEMA)