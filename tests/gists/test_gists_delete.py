"""Tests for DELETE /gists/{gist_id} (Delete a Gist)."""

import pytest

from config import settings
from core import gist_helpers
from core.assertions import assert_common, assert_error


@pytest.mark.smoke
def test_tc_gist_delete_001_verify_that_an_existing_gist_can_be_deleted(github, existing_gist):
    response = gist_helpers.delete_gist(github, existing_gist["id"])

    assert response.status_code == 204
    assert_common(response)
    assert response.text == ""

    get_response = gist_helpers.get_gist(github, existing_gist["id"])
    assert get_response.status_code == 404


@pytest.mark.negative
def test_tc_gist_delete_002_verify_that_a_deleted_gist_cannot_be_retrieved(github, deleted_gist):

    response = gist_helpers.get_gist(github, deleted_gist["id"])

    assert_error(response, 404, "Not Found")


@pytest.mark.negative
def test_tc_gist_delete_003_verify_that_a_non_existent_gist_cannot_be_deleted(github):

    response = gist_helpers.delete_gist(github, settings.NON_EXISTENT_GIST)

    assert_error(response, 404, "Not Found")