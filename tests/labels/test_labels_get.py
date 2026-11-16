"""GET labels (list and by name)."""
import pytest

from config import settings
from config.settings import Endpoints
from core.assertions import assert_common, assert_error, assert_has_more_pages, assert_is_single_page, assert_schema
from core.label_assertions import assert_label_matches
from core.schemas import LABEL_SCHEMA

DEFAULT_LABEL_NAME = "bug"
MINIMUM_LABELS_IN_TEST_REPOSITORY = 12


@pytest.mark.smoke
def test_tc_label_get_001_verify_that_repository_labels_can_be_listed(github):
    response = github.get(Endpoints.LABELS)

    assert response.status_code == 200
    assert_common(response)
    labels = response.json()
    assert isinstance(labels, list) and labels
    for label in labels:
        assert_schema(label, LABEL_SCHEMA)
    assert DEFAULT_LABEL_NAME in [label["name"] for label in labels]


@pytest.mark.negative
def test_tc_label_get_002_verify_that_labels_cannot_be_listed_for_a_nonexistent_repository(github):
    response = github.get(f"/repos/{settings.OWNER}/{settings.NON_EXISTENT_REPO}/labels")
    assert_error(response, 404, "Not Found")


@pytest.mark.boundary
def test_tc_label_get_003_verify_that_label_pagination_returns_the_requested_page_size(github):
    first_page = github.get(Endpoints.LABELS, params={"per_page": 1, "page": 1})
    second_page = github.get(Endpoints.LABELS, params={"per_page": 1, "page": 2})

    assert first_page.status_code == 200
    assert_common(first_page)
    assert len(first_page.json()) == 1
    assert_has_more_pages(first_page)
    assert second_page.status_code == 200
    assert len(second_page.json()) == 1
    assert second_page.json()[0]["name"] != first_page.json()[0]["name"]


@pytest.mark.boundary
def test_tc_label_get_004_verify_that_the_maximum_page_size_returns_all_labels_when_fewer_than_100_exist(github):
    response = github.get(Endpoints.LABELS, params={"per_page": 100})

    assert response.status_code == 200
    assert_common(response)
    assert MINIMUM_LABELS_IN_TEST_REPOSITORY <= len(response.json()) < 100
    assert_is_single_page(response)


@pytest.mark.negative
def test_tc_label_get_006_verify_that_a_nonexistent_label_cannot_be_retrieved(github):
    response = github.get(Endpoints.label("qa-pm-does-not-exist"))
    assert_error(response, 404, "Not Found")


@pytest.mark.smoke
def test_tc_label_get_005_verify_that_an_existing_label_can_be_retrieved_by_name(github, existing_label):
    response = github.get(Endpoints.label(existing_label["name"]))

    assert response.status_code == 200
    assert_common(response)
    assert_label_matches(response.json(), existing_label)
    assert_schema(response.json(), LABEL_SCHEMA)