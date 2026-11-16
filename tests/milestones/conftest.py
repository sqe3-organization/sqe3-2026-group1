"""Fixtures of the Milestones tests. The shared ones (github, anonymous, invalid_client) are in tests/conftest.py."""
import pytest

from core.milestone_helpers import (
    cleanup_milestones,
    create_milestone,
    delete_milestone,
    remove_leftover_milestones,
)


def _test_case_id(request):
    test_name_before_description = request.node.name.split("_verify")[0]
    return test_name_before_description.removeprefix("test_")


@pytest.fixture(scope="session", autouse=True)
def remove_leftover_test_milestones_before_and_after_session(github):
    remove_leftover_milestones(github)
    yield
    remove_leftover_milestones(github)


@pytest.fixture
def milestone_numbers_to_clean_up(github):
    numbers = []
    yield numbers
    cleanup_milestones(github, numbers)


@pytest.fixture
def existing_milestone(github, milestone_numbers_to_clean_up, request):
    milestone = create_milestone(github, _test_case_id(request))
    milestone_numbers_to_clean_up.append(milestone["number"])
    return milestone


@pytest.fixture
def deleted_milestone(github, existing_milestone):
    response = delete_milestone(github, existing_milestone["number"])
    assert response.status_code == 204, f"Precondition failed: could not delete #{existing_milestone['number']} ({response.status_code})"
    return existing_milestone