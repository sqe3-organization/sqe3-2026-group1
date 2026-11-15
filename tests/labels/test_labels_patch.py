"""PATCH /repos/{owner}/{repo}/labels/{name} (Update a label)."""
import pytest

from config.settings import Endpoints
from core import data_factory
from core.assertions import assert_common, assert_error, assert_schema
from core.label_assertions import assert_label_can_be_retrieved, assert_label_does_not_exist, assert_label_matches
from core.schemas import LABEL_SCHEMA


@pytest.mark.negative
def test_tc_label_patch_004_verify_that_a_label_cannot_be_updated_using_a_nonexistent_label_name(github):
    response = github.patch(Endpoints.label("qa-pm-does-not-exist"), json={"color": "E99695"})
    assert_error(response, 404, "Not Found")


@pytest.mark.smoke
def test_tc_label_patch_001_verify_that_the_color_and_description_of_a_label_can_be_updated(github, existing_label):
    new_values = {"color": "E99695", "description": "Updated description for API testing"}
    expected_label = {**existing_label, **new_values}
    response = github.patch(Endpoints.label(existing_label["name"]), json=new_values)

    assert response.status_code == 200
    assert_common(response)
    assert_label_matches(response.json(), expected_label)
    assert_schema(response.json(), LABEL_SCHEMA)
    retrieved_label = github.get(Endpoints.label(existing_label["name"]))
    assert_label_matches(retrieved_label.json(), expected_label)


def test_tc_label_patch_002_verify_that_a_label_can_be_renamed(github, existing_label, label_names_to_clean_up):
    new_name = data_factory.label_name("tc_label_patch_002")
    label_names_to_clean_up.append(new_name)
    response = github.patch(Endpoints.label(existing_label["name"]), json={"new_name": new_name})

    assert response.status_code == 200
    assert_common(response)
    assert response.json()["name"] == new_name
    assert_label_can_be_retrieved(github, new_name)


@pytest.mark.negative
def test_tc_label_patch_003_verify_that_a_renamed_label_cannot_be_retrieved_using_its_old_name(github, renamed_label):
    assert_label_does_not_exist(github, renamed_label.old_name)