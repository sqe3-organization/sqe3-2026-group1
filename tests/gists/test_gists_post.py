"""Tests for POST /gists (Create a Gist)."""

import pytest

from config.settings import Endpoints
from core import data_factory, gist_helpers
from core.assertions import (
    assert_common,
    assert_error,
    assert_error_contains,
    assert_schema,
)
from core.schemas import GIST_SCHEMA


def clean_up_gist_if_created(response, gist_ids_to_clean_up):
    if response.status_code == 201:
        gist_ids_to_clean_up.append(response.json()["id"])


@pytest.mark.smoke
def test_tc_gist_post_001_verify_that_a_gist_can_be_created_with_valid_data(github, gist_ids_to_clean_up):
    description = data_factory.gist_description("tc_gist_post_001")
    content = data_factory.file_content()

    new_gist = {
        "description": description,
        "public": False,
        "files": {"hello.py": {"content": content}}
    }

    response = github.post(Endpoints.GISTS, json=new_gist)

    assert response.status_code == 201
    created_gist = response.json()
    gist_ids_to_clean_up.append(created_gist["id"])

    assert_common(response)
    assert_schema(created_gist, GIST_SCHEMA)
    assert created_gist["description"] == description
    assert created_gist["public"] is False
    assert created_gist["files"]["hello.py"]["content"] == content

    stored_response = gist_helpers.get_gist(github, created_gist["id"])

    assert stored_response.status_code == 200
    assert stored_response.json()["description"] == description


@pytest.mark.negative
@pytest.mark.no_token
def test_tc_gist_post_002_verify_that_a_gist_cannot_be_created_without_a_token(anonymous):
    new_gist = {
        "description": "Must not be created",
        "public": False,
        "files": {"hello.txt": {"content": data_factory.file_content()}}
    }

    response = anonymous.post(Endpoints.GISTS, json=new_gist)

    assert_error(response, 401, "Requires authentication")


@pytest.mark.negative
def test_tc_gist_post_003_verify_that_a_gist_cannot_be_created_without_files(github, gist_ids_to_clean_up):
    response = github.post(
        Endpoints.GISTS,
        json={"description": "Gist without files", "public": False}
    )

    clean_up_gist_if_created(response, gist_ids_to_clean_up)

    assert response.status_code == 422
    assert_error_contains(response, 422, "files")


@pytest.mark.negative
def test_tc_gist_post_004_verify_that_a_gist_cannot_be_created_without_file_content(github, gist_ids_to_clean_up):
    gist_without_content = {
        "description": "Gist without content",
        "public": False,
        "files": {"hello.txt": {}}
    }

    response = github.post(Endpoints.GISTS, json=gist_without_content)

    clean_up_gist_if_created(response, gist_ids_to_clean_up)

    assert response.status_code == 422
    assert_error_contains(response, 422, "content")


@pytest.mark.boundary
def test_tc_gist_post_005_verify_that_a_gist_can_be_created_with_an_empty_filename(github, gist_ids_to_clean_up):
    gist_with_empty_filename = {
        "description": data_factory.gist_description("tc_gist_post_005"),
        "public": False,
        "files": {"": {"content": "Testing an empty filename."}}
    }

    response = github.post(Endpoints.GISTS, json=gist_with_empty_filename)

    assert response.status_code == 201
    created_gist = response.json()
    gist_ids_to_clean_up.append(created_gist["id"])

    assert_common(response)
    assert len(created_gist["files"]) > 0  # GitHub generates a filename.
    assert created_gist["id"]


def test_tc_gist_post_006_verify_that_a_gist_can_be_created_without_a_description(github, gist_ids_to_clean_up):
    gist_without_description = {
        "public": False,
        "files": {"hello.txt": {"content": "Gist without description."}}
    }

    response = github.post(Endpoints.GISTS, json=gist_without_description)

    assert response.status_code == 201
    gist_ids_to_clean_up.append(response.json()["id"])

    assert_common(response)
    assert response.json()["description"] is None


def test_tc_gist_post_007_verify_that_a_gist_is_private_when_public_is_not_sent(github, gist_ids_to_clean_up):
    gist_without_public_field = {
        "description": data_factory.gist_description("tc_gist_post_007"),
        "files": {"hello.txt": {"content": "Testing default visibility."}}
    }

    response = github.post(Endpoints.GISTS, json=gist_without_public_field)

    assert response.status_code == 201
    gist_ids_to_clean_up.append(response.json()["id"])

    assert_common(response)
    assert response.json()["public"] is False


def test_tc_gist_post_008_verify_that_a_gist_can_be_created_with_multiple_files(github, gist_ids_to_clean_up):
    gist_with_two_files = {
        "description": data_factory.gist_description("tc_gist_post_008"),
        "public": False,
        "files": gist_helpers.build_files("hello.txt", "notes.txt")
    }

    response = github.post(Endpoints.GISTS, json=gist_with_two_files)

    assert response.status_code == 201
    created_gist = response.json()
    gist_ids_to_clean_up.append(created_gist["id"])

    assert_common(response)
    assert set(created_gist["files"]) == {"hello.txt", "notes.txt"}


def test_tc_gist_post_009_verify_that_a_public_gist_can_be_created(github, gist_ids_to_clean_up):
    public_gist = {
        "description": data_factory.gist_description("tc_gist_post_009"),
        "public": True,
        "files": gist_helpers.build_files("public.txt")
    }

    response = github.post(Endpoints.GISTS, json=public_gist)

    assert response.status_code == 201
    created_gist = response.json()
    gist_ids_to_clean_up.append(created_gist["id"])

    assert_common(response)
    assert_schema(created_gist, GIST_SCHEMA)
    assert created_gist["public"] is True