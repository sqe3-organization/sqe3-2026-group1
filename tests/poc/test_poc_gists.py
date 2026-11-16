"""POC 4 - What the Gists tests need from the tools.

Checks, before migrating the Gist test cases, the details that differ from the other modules:
the body with a nested `files` object (null removes a file), the public Gists list (no token),
the 404 error body, and DELETE (204 without a body). Only the last one needs a token.
"""
import pytest
import requests

from config import settings
from config.settings import Endpoints
from core import gist_helpers
from core.assertions import assert_schema
from core.schemas import ERROR_SCHEMA


def test_json_parameter_serializes_null_to_remove_a_file():
    prepared = requests.Request("PATCH", "https://example.test", json={"files": {"hello.py": None}}).prepare()

    assert prepared.headers["Content-Type"] == "application/json"
    assert b'"hello.py": null' in prepared.body or b'"hello.py":null' in prepared.body


def test_public_gists_can_be_listed_without_a_token_and_per_page_is_respected(anonymous):
    response = anonymous.get(Endpoints.PUBLIC_GISTS, params={"per_page": 2})

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) <= 2


def test_requests_does_not_raise_on_a_404_and_the_error_has_the_error_schema(anonymous):
    response = anonymous.get(Endpoints.gist(settings.NON_EXISTENT_GIST))

    assert response.status_code == 404
    assert_schema(response.json(), ERROR_SCHEMA)


@pytest.mark.skipif(not settings.TOKEN, reason="GITHUB_TOKEN is empty in .env")
def test_delete_returns_204_with_an_empty_body(github):
    gist = gist_helpers.create_gist(github, "tc_poc_gist_delete")

    response = gist_helpers.delete_gist(github, gist["id"])

    assert response.status_code == 204
    assert response.text == ""
    assert gist_helpers.get_gist(github, gist["id"]).status_code == 404
