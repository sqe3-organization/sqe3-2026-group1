
"""Pre and postconditions for the Milestones tests, used by tests/milestones/conftest.py
and by the module fixture of test_milestones_get.py.

They replace the Setup and Teardown folders of the Postman collection.
"""
from config import settings
from config.settings import Endpoints
from core import data_factory
from core.cleanup_logging import log_cleanup_result
from core.logger import get_logger

logger = get_logger(__name__)

TEST_PREFIX = "qa-pm-"


def create_milestone(client, tc_id, **extra):
    payload = {
        "title": data_factory.milestone_title(tc_id),
        "description": "Milestone created by a pytest test",
        "state": "open",
        "due_on": "2026-12-31T00:00:00Z",
        **extra,
    }
    response = client.post(Endpoints.MILESTONES, json=payload)
    assert response.status_code == 201, f"Precondition failed: could not create the milestone ({response.status_code})"
    created_milestone = response.json()
    logger.info("Milestone #%d created with title %s", created_milestone["number"], created_milestone["title"])
    return created_milestone


def delete_milestone(client, number):
    return client.delete(Endpoints.milestone(number))


def cleanup_milestones(client, numbers):
    """Deletes the milestones the test created. 404 is fine: the test may have deleted it.
    It does not raise: a failed cleanup must not hide the real result of the test."""
    for number in numbers:
        response = delete_milestone(client, number)
        log_cleanup_result(logger, f"milestone #{number}", response, action_done="deleted")
    numbers.clear()


def remove_leftover_milestones(client):
    """Session cleanup: deletes any milestone whose title starts with qa-pm-."""
    if not settings.TOKEN:
        return
    response = client.get(Endpoints.MILESTONES, params={"state": "all", "per_page": 100})
    if response.status_code != 200:
        logger.warning("Could not list the milestones to look for leftovers | status=%s", response.status_code)
        return
    for milestone in response.json():
        if milestone["title"].startswith(TEST_PREFIX):
            delete_milestone(client, milestone["number"])
            logger.warning("Leftover milestone from a previous run deleted: #%d", milestone["number"])
