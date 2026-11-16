"""POC 3 - What the Labels and Milestones tests need from the tools.

Checks, before migrating the 49 test cases, the details that differ from Issues: the Link header
(pagination), label names with spaces, how `json=` builds the request, and DELETE (204 without a body).
Only the last one needs a token.
"""
import pytest

from config import settings
from config.settings import Endpoints
from core import label_helpers
from core.assertions import assert_no_content


def test_requests_parses_the_link_header_of_the_pagination(anonymous):
    response = anonymous.get(Endpoints.LABELS, params={"per_page": 1, "page": 1})

    assert response.status_code == 200
    next_page_url = response.links["next"]["url"]
    assert "page=2" in next_page_url
    assert "last" in response.links


def test_label_names_with_spaces_are_url_encoded(anonymous):
    path = Endpoints.label("good first issue")

    assert path.endswith("/labels/good%20first%20issue")
    response = anonymous.get(path)
    assert response.status_code == 200
    assert response.json()["name"] == "good first issue"


def test_json_parameter_serializes_the_body_and_sets_the_content_type(anonymous):
    rejected_response = anonymous.post(Endpoints.LABELS, json={"name": "qa-pm-poc-json", "color": "1D76DB"})
    sent_request = rejected_response.request

    assert rejected_response.status_code == 401
    assert sent_request.headers["Content-Type"] == "application/json"
    assert b'"name": "qa-pm-poc-json"' in sent_request.body or b'"name":"qa-pm-poc-json"' in sent_request.body


@pytest.mark.skipif(not settings.TOKEN, reason="GITHUB_TOKEN is empty in .env")
def test_delete_returns_204_with_an_empty_body(github):
    label = label_helpers.create_label(github, "tc_poc_delete")

    response = github.delete(Endpoints.label(label["name"]))

    assert_no_content(response)
    assert github.get(Endpoints.label(label["name"])).status_code == 404