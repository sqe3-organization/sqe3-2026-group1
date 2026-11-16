"""Tests for GET /gists/{gist_id} (Get a Gist)."""

import pytest

from core import gist_helpers
from core.assertions import assert_common, assert_error, assert_schema
from core.schemas import GIST_SCHEMA


@pytest.mark.smoke
def test_tc_gist_get_001_verify_that_an_existing_gist_can_be_retrieved(github, existing_gist):
    response = gist_helpers.get_gist(github, existing_gist["id"])

    assert response.status_code == 200

    retrieved_gist = response.json()

    assert_common(response)
    assert_schema(retrieved_gist, GIST_SCHEMA)
    assert retrieved_gist["id"] == existing_gist["id"]
    assert gist_helpers.MAIN_FILE in retrieved_gist["files"]


@pytest.mark.negative
def test_tc_gist_get_002_verify_that_a_deleted_gist_cannot_be_retrieved(github, deleted_gist):
    response = gist_helpers.get_gist(github, deleted_gist["id"])

    assert_error(response, 404, "Not Found")


def test_tc_gist_get_003_verify_that_a_public_gist_can_be_retrieved_without_a_token(anonymous, existing_public_gist):
    response = gist_helpers.get_gist(anonymous, existing_public_gist["id"])

    assert response.status_code == 200

    retrieved_gist = response.json()

    assert_common(response)
    assert retrieved_gist["public"] is True
    assert "public.txt" in retrieved_gist["files"]


def test_tc_gist_get_004_verify_that_a_gist_with_multiple_files_can_be_retrieved(github, existing_gist):
    response = gist_helpers.get_gist(github, existing_gist["id"])

    assert response.status_code == 200
    assert_common(response)
    assert len(response.json()["files"]) > 1