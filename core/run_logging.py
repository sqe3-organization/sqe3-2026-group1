"""Turns the pytest reports of one test into the result line of the log.

pytest creates one report for each phase of a test: setup (fixtures), call (the test itself)
and teardown (cleanup). The result of the test is decided when its three phases are known,
so that a cleanup that fails is also visible.

The line written to the log has this shape, and the log report (core/log_report.py) reads it:

    RESULT PASSED | 312 ms | tests/issues/test_post.py::test_create
    RESULT FAILED | 540 ms | tests/issues/test_patch.py::test_state | reason=assert 200 == 422
"""
import logging
from dataclasses import dataclass

PASSED = "PASSED"
FAILED = "FAILED"
SKIPPED = "SKIPPED"
ERROR = "ERROR"

LOG_LEVEL_BY_OUTCOME = {
    PASSED: logging.INFO,
    SKIPPED: logging.WARNING,
    FAILED: logging.ERROR,
    ERROR: logging.ERROR,
}

RESULT_LINE_PREFIX = "RESULT"
RESULT_FIELD_SEPARATOR = " | "
REASON_FIELD_PREFIX = "reason="
MAX_REASON_CHARACTERS = 200
MILLISECONDS_PER_SECOND = 1000


@dataclass(frozen=True)
class ExecutedTestResult:
    """What happened to one test, summed over its setup, call and teardown."""

    outcome: str
    duration_ms: int
    reason: str


def first_line_of(text):
    """The first line of a text, or an empty string when the text is empty."""
    lines = text.strip().splitlines()
    return lines[0] if lines else ""


def describe_reason(report):
    """Short explanation of why a phase did not pass (empty when it passed)."""
    if report.passed:
        return ""
    if report.skipped and isinstance(report.longrepr, tuple):
        full_reason = report.longrepr[2]
    else:
        crash = getattr(report.longrepr, "reprcrash", None)
        full_reason = crash.message if crash else str(report.longrepr)
    return first_line_of(full_reason)[:MAX_REASON_CHARACTERS]


def decide_outcome(phase_reports):
    """Returns the outcome of the test and the report of the phase that explains it."""
    setup_report = phase_reports["setup"]
    call_report = phase_reports.get("call")
    teardown_report = phase_reports["teardown"]

    if setup_report.failed:
        return ERROR, setup_report
    if setup_report.skipped:
        return SKIPPED, setup_report
    if call_report.failed:
        return FAILED, call_report
    if teardown_report.failed:
        return ERROR, teardown_report
    if call_report.skipped:
        return SKIPPED, call_report
    return PASSED, call_report


def summarize_test_result(phase_reports):
    """phase_reports: the pytest reports of one test, indexed by phase (setup, call, teardown)."""
    outcome, explaining_report = decide_outcome(phase_reports)
    total_seconds = sum(report.duration for report in phase_reports.values())
    return ExecutedTestResult(
        outcome=outcome,
        duration_ms=round(total_seconds * MILLISECONDS_PER_SECOND),
        reason=describe_reason(explaining_report),
    )


def build_result_message(test_id, result):
    """The message of the RESULT line of a test."""
    fields = [RESULT_LINE_PREFIX + " " + result.outcome, f"{result.duration_ms} ms", test_id]
    if result.reason:
        fields.append(REASON_FIELD_PREFIX + result.reason)
    return RESULT_FIELD_SEPARATOR.join(fields)
