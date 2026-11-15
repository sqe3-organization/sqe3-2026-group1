"""DELETE /repos/{owner}/{repo}/milestones/{number} (Delete a milestone)."""
import pytest

from config import settings
from config.settings import Endpoints
from core.assertions import assert_error, assert_no_content


@pytest.mark.negative
def test_tc_milestone_delete_003_verify_that_a_nonexistent_milestone_cannot_be_deleted(github):
    response = github.delete(Endpoints.milestone(settings.NON_EXISTENT_MILESTONE))
    assert_error(response, 404, "Not Found")


@pytest.mark.smoke
def test_tc_milestone_delete_001_verify_that_an_existing_milestone_can_be_deleted(github, existing_milestone):
    response = github.delete(Endpoints.milestone(existing_milestone["number"]))
    assert_no_content(response)


@pytest.mark.negative
def test_tc_milestone_delete_002_verify_that_a_deleted_milestone_can_no_longer_be_retrieved(github, deleted_milestone):
    response = github.get(Endpoints.milestone(deleted_milestone["number"]))
    assert_error(response, 404, "Not Found")