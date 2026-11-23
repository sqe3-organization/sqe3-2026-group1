
"""Log lines of the cleanup (postcondition) of every module, so they all use the same levels and wording.

    INFO     the cleanup did what it had to do          Cleanup: label qa-pm-x deleted
    WARNING  the resource was already gone (tolerated)  Cleanup: label qa-pm-x was already deleted
    ERROR    the cleanup failed                         Cleanup failed for label qa-pm-x | expected status 204, got 500

The cleanup never raises, so a failed cleanup cannot hide the real result of the test.
That is why its failures are logged as ERROR instead of being reported by an assertion.
"""
from dataclasses import dataclass
from http import HTTPStatus


@dataclass(frozen=True)
class CleanupRule:
    """What a cleanup does and which statuses it expects.

    action_done: the past tense of the cleanup action, for example "deleted".
    expected_status: the status of a cleanup that worked.
    tolerated_status: a status that is not a failure (the resource was already gone). None if there is none.
    """

    action_done: str
    expected_status: int = HTTPStatus.NO_CONTENT
    tolerated_status: int = HTTPStatus.NOT_FOUND


DELETE_RULE = CleanupRule(action_done="deleted")
CLOSE_AS_NOT_PLANNED_RULE = CleanupRule(
    action_done="closed as not_planned",
    expected_status=HTTPStatus.OK,
    tolerated_status=None,
)


def log_cleanup_result(logger, resource_description, response, rule=DELETE_RULE):
    """Logs what happened when a helper cleaned up one resource, for example "label qa-pm-x"."""
    if response.status_code == rule.expected_status:
        logger.info("Cleanup: %s %s", resource_description, rule.action_done)
    elif response.status_code == rule.tolerated_status:
        logger.warning("Cleanup: %s was already deleted", resource_description)
    else:
        logger.error(
            "Cleanup failed for %s | expected status %s, got %s",
            resource_description,
            int(rule.expected_status),
            response.status_code,
        )
