
"""Unit tests of the log lines written by the helpers of each module (layer 2).

They use a fake client, so they do not call GitHub and run without a token.
"""
from types import SimpleNamespace

import pytest

from core import issue_helpers, label_helpers, repo_helpers
from core.cleanup_logging import log_cleanup_result
from core.logger import configure_logging, shutdown_logging

pytestmark = pytest.mark.no_token

LABEL_NAME = "qa-pm-label-post-001-abc123"


class FakeClient:
    """Answers every request with the same status code and body."""

    def __init__(self, status_code, body=None):
        self.response = SimpleNamespace(status_code=status_code, json=lambda: body)

    def post(self, path, json=None):
        return self.response

    def patch(self, path, json=None):
        return self.response

    def delete(self, path):
        return self.response


def read_log_file(log_file_path):
    shutdown_logging()
    return log_file_path.read_text(encoding="utf-8")


def test_creating_a_label_is_logged_as_info_with_its_name(tmp_path):
    log_file_path = configure_logging("INFO", tmp_path)

    label_helpers.create_label(FakeClient(201, {"name": LABEL_NAME}), "tc_label_post_001")

    assert f"INFO    | Label created with name {LABEL_NAME}" in read_log_file(log_file_path)


def test_creating_an_issue_is_logged_as_info_with_its_number(tmp_path):
    log_file_path = configure_logging("INFO", tmp_path)

    issue_helpers.create_issue(FakeClient(201, {"number": 7, "title": "TC_ISS_POST_001 - Title"}), "TC_ISS_POST_001")

    assert "INFO    | Issue #7 created with title TC_ISS_POST_001 - Title" in read_log_file(log_file_path)


def test_a_failed_precondition_still_raises_and_logs_nothing_as_info(tmp_path):
    log_file_path = configure_logging("INFO", tmp_path)

    with pytest.raises(AssertionError, match="Precondition failed"):
        label_helpers.create_label(FakeClient(403), "tc_label_post_001")

    assert "Label created" not in read_log_file(log_file_path)


def test_cleanup_logs_info_when_the_resource_is_deleted(tmp_path):
    log_file_path = configure_logging("INFO", tmp_path)
    names = [LABEL_NAME]

    label_helpers.cleanup_labels(FakeClient(204), names)

    assert f"INFO    | Cleanup: label {LABEL_NAME} deleted" in read_log_file(log_file_path)
    assert names == []


def test_cleanup_logs_a_warning_when_the_resource_was_already_deleted(tmp_path):
    log_file_path = configure_logging("INFO", tmp_path)

    label_helpers.cleanup_labels(FakeClient(404), [LABEL_NAME])

    assert f"WARNING | Cleanup: label {LABEL_NAME} was already deleted" in read_log_file(log_file_path)


def test_cleanup_logs_an_error_and_does_not_raise_when_it_fails(tmp_path):
    log_file_path = configure_logging("INFO", tmp_path)
    names = [LABEL_NAME]

    label_helpers.cleanup_labels(FakeClient(500), names)

    assert f"ERROR   | Cleanup failed for label {LABEL_NAME} | expected status 204, got 500" in read_log_file(
        log_file_path
    )
    assert names == []


def test_issue_cleanup_does_not_tolerate_a_missing_issue(tmp_path):
    log_file_path = configure_logging("INFO", tmp_path)

    issue_helpers.cleanup_issues(FakeClient(404), [7])

    assert "ERROR   | Cleanup failed for issue #7 | expected status 200, got 404" in read_log_file(log_file_path)


def test_cleanup_of_a_repository_that_is_not_a_test_repository_is_skipped_with_a_warning(tmp_path):
    log_file_path = configure_logging("INFO", tmp_path)

    repo_helpers.cleanup_repos(FakeClient(204), ["my-personal-repository"])

    log_content = read_log_file(log_file_path)
    assert "WARNING | Cleanup skipped: repository my-personal-repository is not a test repository" in log_content
    assert "deleted" not in log_content


def test_log_cleanup_result_uses_the_action_given_by_the_caller(tmp_path):
    log_file_path = configure_logging("INFO", tmp_path)
    logger = label_helpers.logger

    log_cleanup_result(logger, "issue #3", SimpleNamespace(status_code=200), "closed as not_planned", expected_status=200)

    assert "INFO    | Cleanup: issue #3 closed as not_planned" in read_log_file(log_file_path)


def test_waiting_for_a_condition_that_never_happens_logs_a_warning(tmp_path):
    log_file_path = configure_logging("INFO", tmp_path)

    result = issue_helpers.wait_until(lambda: False, timeout=0.01, interval=0.001)

    assert result is False
    assert "WARNING | The condition was still not met after waiting 0.01 seconds" in read_log_file(log_file_path)
