"""Unit tests of the result line of each test (core/run_logging.py).

They use fake pytest reports, so they do not call GitHub and run without a token.
"""
from types import SimpleNamespace

import pytest

from core.run_logging import (
    ERROR,
    FAILED,
    MAX_REASON_CHARACTERS,
    PASSED,
    SKIPPED,
    ExecutedTestResult,
    build_result_message,
    summarize_test_result,
)

pytestmark = pytest.mark.no_token

TEST_ID = "tests/issues/test_post.py::test_create"


def build_report(outcome, duration=0.1, longrepr=None):
    """A fake pytest report of one phase. outcome: "passed", "failed" or "skipped"."""
    return SimpleNamespace(
        passed=outcome == "passed",
        failed=outcome == "failed",
        skipped=outcome == "skipped",
        duration=duration,
        longrepr=longrepr,
    )


def build_phase_reports(setup="passed", call="passed", teardown="passed", call_longrepr=None):
    reports = {"setup": build_report(setup), "teardown": build_report(teardown)}
    if call is not None:
        reports["call"] = build_report(call, longrepr=call_longrepr)
    return reports


def failure_with_message(message):
    return SimpleNamespace(reprcrash=SimpleNamespace(message=message))


def test_a_test_that_passes_all_its_phases_is_passed():
    result = summarize_test_result(build_phase_reports())

    assert result == ExecutedTestResult(outcome=PASSED, duration_ms=300, reason="")


def test_a_failed_call_is_failed_and_keeps_the_first_line_of_the_reason():
    reports = build_phase_reports(
        call="failed", call_longrepr=failure_with_message("assert 200 == 422\n  +  where 200 = ...")
    )

    result = summarize_test_result(reports)

    assert result.outcome == FAILED
    assert result.reason == "assert 200 == 422"


def test_a_failed_setup_is_an_error_even_though_the_test_never_ran():
    reports = build_phase_reports(setup="failed", call=None)
    reports["setup"].longrepr = failure_with_message("Precondition failed: could not create the issue")

    result = summarize_test_result(reports)

    assert result.outcome == ERROR
    assert result.reason == "Precondition failed: could not create the issue"


def test_a_failed_cleanup_turns_a_passed_test_into_an_error():
    reports = build_phase_reports(teardown="failed")
    reports["teardown"].longrepr = failure_with_message("cleanup failed")

    assert summarize_test_result(reports).outcome == ERROR


def test_a_test_skipped_in_setup_keeps_the_skip_reason():
    reports = build_phase_reports(setup="skipped", call=None)
    reports["setup"].longrepr = ("tests/conftest.py", 20, "Skipped: GITHUB_TOKEN is empty in .env")

    result = summarize_test_result(reports)

    assert result.outcome == SKIPPED
    assert result.reason == "Skipped: GITHUB_TOKEN is empty in .env"


def test_the_duration_adds_up_setup_call_and_teardown():
    reports = build_phase_reports()
    reports["setup"].duration = 0.5
    reports["call"].duration = 1.25
    reports["teardown"].duration = 0.25

    assert summarize_test_result(reports).duration_ms == 2000


def test_a_long_reason_is_shortened():
    reports = build_phase_reports(call="failed", call_longrepr=failure_with_message("x" * 1000))

    assert len(summarize_test_result(reports).reason) == MAX_REASON_CHARACTERS


def test_the_result_message_of_a_passed_test_has_no_reason():
    result = ExecutedTestResult(outcome=PASSED, duration_ms=312, reason="")

    assert build_result_message(TEST_ID, result) == f"RESULT PASSED | 312 ms | {TEST_ID}"


def test_the_result_message_of_a_failed_test_ends_with_the_reason():
    result = ExecutedTestResult(outcome=FAILED, duration_ms=540, reason="assert 200 == 422")

    assert build_result_message(TEST_ID, result) == f"RESULT FAILED | 540 ms | {TEST_ID} | reason=assert 200 == 422"
