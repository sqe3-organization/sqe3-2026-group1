
"""Log lines of the cleanup (postcondition) of every module, so they all use the same levels and wording.

    INFO     the cleanup did what it had to do          Cleanup: label qa-pm-x deleted
    WARNING  the resource was already gone (tolerated)  Cleanup: label qa-pm-x was already deleted
    ERROR    the cleanup failed                         Cleanup failed for label qa-pm-x | expected status 204, got 500

The cleanup never raises, so a failed cleanup cannot hide the real result of the test.
That is why its failures are logged as ERROR instead of being reported by an assertion.
"""
from http import HTTPStatus


def log_cleanup_result(
    logger,
    resource_description,
    response,
    action_done,
    expected_status=HTTPStatus.NO_CONTENT,
    tolerated_status=HTTPStatus.NOT_FOUND,
):
    """Logs what happened when a helper cleaned up one resource.

    resource_description: what was cleaned up, for example "label qa-pm-x".
    action_done: the past tense of the cleanup action, for example "deleted" or "closed as not_planned".
    tolerated_status: a status that is not a failure (the resource was already gone). None if there is none.
    """
    if response.status_code == expected_status:
        logger.info("Cleanup: %s %s", resource_description, action_done)
    elif response.status_code == tolerated_status:
        logger.warning("Cleanup: %s was already deleted", resource_description)
    else:
        logger.error(
            "Cleanup failed for %s | expected status %s, got %s",
            resource_description,
            int(expected_status),
            response.status_code,
        )
