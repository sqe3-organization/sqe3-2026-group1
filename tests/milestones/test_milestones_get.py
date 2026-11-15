"""GET milestones (list, filters, sorting, pagination and by number)."""
from datetime import datetime

import pytest

from config import settings
from config.settings import Endpoints
from core.assertions import assert_common, assert_error, assert_has_more_pages, assert_is_single_page, assert_schema
from core.milestone_helpers import cleanup_milestones, create_milestone
from core.schemas import MILESTONE_SCHEMA

PAGE_BEYOND_THE_LAST_ONE = 100


@pytest.fixture(scope="module")
def read_only_milestones(github):
    first_open = create_milestone(github, "tc_milestone_get_open_1", due_on="2026-12-01T00:00:00Z")
    second_open = create_milestone(github, "tc_milestone_get_open_2", due_on="2027-01-15T00:00:00Z")
    closed = create_milestone(github, "tc_milestone_get_closed", state="closed", due_on="2026-11-20T00:00:00Z")
    yield {"first_open": first_open, "second_open": second_open, "closed": closed}
    cleanup_milestones(github, [first_open["number"], second_open["number"], closed["number"]])


def _titles_of(response):
    return [milestone["title"] for milestone in response.json()]


def _parse_github_timestamp(timestamp):
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


def _due_dates_of_milestones_that_have_one(response):
    return [_parse_github_timestamp(milestone["due_on"]) for milestone in response.json() if milestone["due_on"]]


@pytest.mark.negative
def test_tc_milestone_get_011_verify_that_a_nonexistent_milestone_cannot_be_retrieved(github):
    response = github.get(Endpoints.milestone(settings.NON_EXISTENT_MILESTONE))
    assert_error(response, 404, "Not Found")


@pytest.mark.boundary
def test_tc_milestone_get_009_verify_that_requesting_a_page_beyond_the_available_results_returns_an_empty_list(github):
    response = github.get(Endpoints.MILESTONES, params={"state": "all", "per_page": 1, "page": PAGE_BEYOND_THE_LAST_ONE})

    assert response.status_code == 200
    assert_common(response)
    assert response.json() == []


@pytest.mark.smoke
def test_tc_milestone_get_001_verify_that_repository_milestones_can_be_listed(github, read_only_milestones):
    response = github.get(Endpoints.MILESTONES)

    assert response.status_code == 200
    assert_common(response)
    assert isinstance(response.json(), list) and response.json()
    for milestone in response.json():
        assert {"number", "title", "state"} <= milestone.keys()
    open_titles = {read_only_milestones["first_open"]["title"], read_only_milestones["second_open"]["title"]}
    assert open_titles <= set(_titles_of(response))


def test_tc_milestone_get_002_verify_that_milestones_can_be_filtered_by_open_state(github, read_only_milestones):
    response = github.get(Endpoints.MILESTONES, params={"state": "open"})

    assert response.status_code == 200
    assert_common(response)
    assert all(milestone["state"] == "open" for milestone in response.json())
    assert read_only_milestones["first_open"]["title"] in _titles_of(response)
    assert read_only_milestones["closed"]["title"] not in _titles_of(response)


def test_tc_milestone_get_003_verify_that_milestones_can_be_filtered_by_closed_state(github, read_only_milestones):
    response = github.get(Endpoints.MILESTONES, params={"state": "closed"})

    assert response.status_code == 200
    assert_common(response)
    assert all(milestone["state"] == "closed" for milestone in response.json())
    assert read_only_milestones["closed"]["title"] in _titles_of(response)
    assert read_only_milestones["first_open"]["title"] not in _titles_of(response)


def test_tc_milestone_get_004_verify_that_all_milestones_can_be_listed_regardless_of_their_state(github, read_only_milestones):
    response = github.get(Endpoints.MILESTONES, params={"state": "all"})

    assert response.status_code == 200
    assert_common(response)
    assert {"open", "closed"} <= {milestone["state"] for milestone in response.json()}
    one_open_and_one_closed_title = {read_only_milestones["first_open"]["title"], read_only_milestones["closed"]["title"]}
    assert one_open_and_one_closed_title <= set(_titles_of(response))


def test_tc_milestone_get_005_verify_that_milestones_can_be_sorted_by_due_date_in_ascending_order(github, read_only_milestones):
    response = github.get(Endpoints.MILESTONES, params={"state": "all", "sort": "due_on", "direction": "asc"})

    assert response.status_code == 200
    assert_common(response)
    due_dates = _due_dates_of_milestones_that_have_one(response)
    assert len(due_dates) >= 2
    assert due_dates == sorted(due_dates)


def test_tc_milestone_get_006_verify_that_milestones_can_be_sorted_by_due_date_in_descending_order(github, read_only_milestones):
    response = github.get(Endpoints.MILESTONES, params={"state": "all", "sort": "due_on", "direction": "desc"})

    assert response.status_code == 200
    assert_common(response)
    due_dates = _due_dates_of_milestones_that_have_one(response)
    assert len(due_dates) >= 2
    assert due_dates == sorted(due_dates, reverse=True)


@pytest.mark.boundary
def test_tc_milestone_get_007_verify_that_milestone_pagination_returns_the_requested_page_size(github, read_only_milestones):
    first_page = github.get(Endpoints.MILESTONES, params={"per_page": 1, "page": 1})
    second_page = github.get(Endpoints.MILESTONES, params={"per_page": 1, "page": 2})

    assert first_page.status_code == 200
    assert_common(first_page)
    assert len(first_page.json()) == 1
    assert_has_more_pages(first_page)
    assert second_page.status_code == 200
    assert len(second_page.json()) == 1
    assert second_page.json()[0]["number"] != first_page.json()[0]["number"]


@pytest.mark.boundary
def test_tc_milestone_get_008_verify_that_the_maximum_page_size_returns_all_milestones_when_fewer_than_100_exist(github, read_only_milestones):
    response = github.get(Endpoints.MILESTONES, params={"per_page": 100})

    assert response.status_code == 200
    assert_common(response)
    assert len(response.json()) < 100
    open_titles = {read_only_milestones["first_open"]["title"], read_only_milestones["second_open"]["title"]}
    assert open_titles <= set(_titles_of(response))
    assert_is_single_page(response)


@pytest.mark.smoke
def test_tc_milestone_get_010_verify_that_an_existing_milestone_can_be_retrieved_by_number(github, read_only_milestones):
    expected_milestone = read_only_milestones["first_open"]
    response = github.get(Endpoints.milestone(expected_milestone["number"]))

    assert response.status_code == 200
    assert_common(response)
    assert response.json()["number"] == expected_milestone["number"]
    assert response.json()["title"] == expected_milestone["title"]
    assert response.json()["state"] == "open"
    assert_schema(response.json(), MILESTONE_SCHEMA)