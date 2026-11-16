"""Tests for PATCH /gists/{gist_id} (Update a Gist).
Each test starts with its own Gist containing two files: hello.py and keep.txt.
"""

import pytest

from config import settings
from config.settings import Endpoints
from core import data_factory, gist_helpers
from core.assertions import assert_common, assert_error, assert_schema
from core.gist_helpers import MAIN_FILE, SECOND_FILE
from core.schemas import GIST_SCHEMA


def test_tc_gist_patch_001_verify_that_the_description_of_a_gist_can_be_updated(github, existing_gist):
    new_description = data_factory.gist_description("tc_gist_patch_001")

    response = github.patch(
        Endpoints.gist(existing_gist["id"]),
        json={"description": new_description}
    )

    assert response.status_code == 200
    assert_common(response)
    assert_schema(response.json(), GIST_SCHEMA)
    assert response.json()["description"] == new_description

    stored_response = gist_helpers.get_gist(github, existing_gist["id"])

    assert stored_response.status_code == 200
    assert stored_response.json()["description"] == new_description


def test_tc_gist_patch_002_verify_that_the_content_of_a_file_can_be_updated(github, existing_gist):
    new_content = data_factory.file_content()

    response = github.patch(
        Endpoints.gist(existing_gist["id"]),
        json={"files": {MAIN_FILE: {"content": new_content}}}
    )

    assert response.status_code == 200
    assert_common(response)
    assert response.json()["files"][MAIN_FILE]["content"] == new_content

    stored_response = gist_helpers.get_gist(github, existing_gist["id"])

    assert stored_response.status_code == 200
    assert stored_response.json()["files"][MAIN_FILE]["content"] == new_content


def test_tc_gist_patch_003_verify_that_a_file_of_a_gist_can_be_renamed(github, existing_gist):
    new_name = "gistsrename.txt"

    response = github.patch(
        Endpoints.gist(existing_gist["id"]),
        json={"files": {MAIN_FILE: {"filename": new_name}}}
    )

    assert response.status_code == 200
    assert_common(response)
    assert new_name in response.json()["files"]
    assert MAIN_FILE not in response.json()["files"]

    stored_response = gist_helpers.get_gist(github, existing_gist["id"])

    assert stored_response.status_code == 200
    stored_files = stored_response.json()["files"]

    assert new_name in stored_files
    assert MAIN_FILE not in stored_files


def test_tc_gist_patch_004_verify_that_a_file_can_be_removed_from_a_gist(github, existing_gist):
    response = github.patch(
        Endpoints.gist(existing_gist["id"]),
        json={"files": {MAIN_FILE: None}}
    )

    assert response.status_code == 200, response.text
    assert_common(response)
    assert MAIN_FILE not in response.json()["files"]
    assert SECOND_FILE in response.json()["files"]

    stored_response = gist_helpers.get_gist(github, existing_gist["id"])

    assert stored_response.status_code == 200
    stored_files = stored_response.json()["files"]

    assert MAIN_FILE not in stored_files
    assert SECOND_FILE in stored_files


def test_tc_gist_patch_005_verify_that_a_renamed_file_can_be_removed_from_a_gist(github, existing_gist):
    new_name = "gistsrename.txt"

    rename = github.patch(
        Endpoints.gist(existing_gist["id"]),
        json={"files": {MAIN_FILE: {"filename": new_name}}}
    )

    assert rename.status_code == 200, (
        f"Precondition failed: could not rename the file ({rename.status_code})"
    )

    response = github.patch(
        Endpoints.gist(existing_gist["id"]),
        json={"files": {new_name: None}}
    )

    assert response.status_code == 200, response.text
    assert_common(response)
    assert new_name not in response.json()["files"]
    assert SECOND_FILE in response.json()["files"]


def test_tc_gist_patch_006_verify_that_a_gist_can_be_updated_with_an_empty_body(github, existing_gist):
    response = github.patch(
        Endpoints.gist(existing_gist["id"]),
        json={}
    )

    assert response.status_code == 200
    assert_common(response)
    assert response.json()["id"] == existing_gist["id"]
    assert response.json()["files"]


@pytest.mark.negative
def test_tc_gist_patch_007_verify_that_a_non_existent_gist_cannot_be_updated(github):
    response = github.patch(
        Endpoints.gist(settings.NON_EXISTENT_GIST),
        json={"description": "Does not exist"}
    )

    assert_error(response, 404, "Not Found")