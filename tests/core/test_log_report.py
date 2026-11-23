
"""Unit tests of the report generated from the log file (core/log_report.py).

They write small log files in a temporary folder, so they do not call GitHub and run without a token.
"""
import logging

import pytest

from core import log_report, run_logging
from core.log_report import (
    LoggedTestResult,
    RequestRecord,
    count_outcomes,
    find_newest_log_file,
    generate_report,
    group_results_by_module,
    main,
    parse_log_line,
    parse_request_record,
    parse_test_result,
    pass_rate_percentage,
    slowest_requests,
    summarize_run,
)
from core.logger import configure_logging, get_file_only_logger, get_logger, shutdown_logging

pytestmark = pytest.mark.no_token

LOG_FILE_NAME = "test_run_20261122_220008.log"
TEST_ID = "tests/labels/test_labels_post.py::test_create"


def build_log_line(level, message, worker="main", host="PC-TEAM", second=8):
    """One line written in the team format of the log."""
    return f"2026-11-22 22:00:{second:02d},100 | {host} | {worker} | {level:<7} | {message}"


def write_log_file(directory, *lines):
    log_file_path = directory / LOG_FILE_NAME
    log_file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return log_file_path


def build_result_line(outcome, test_id=TEST_ID, duration_ms=100, reason=""):
    result = run_logging.ExecutedTestResult(outcome=outcome, duration_ms=duration_ms, reason=reason)
    level = logging.getLevelName(run_logging.LOG_LEVEL_BY_OUTCOME[outcome])
    return build_log_line(level, run_logging.build_result_message(test_id, result))


# ----------------------------------------------------------------- reading one line
def test_a_line_in_the_team_format_is_split_in_its_fields():
    entry = parse_log_line(build_log_line("WARNING", "Cleanup: label x was already deleted", worker="gw2"))

    assert (entry.host, entry.worker, entry.level) == ("PC-TEAM", "gw2", "WARNING")
    assert entry.message == "Cleanup: label x was already deleted"


@pytest.mark.parametrize(
    "line_that_is_not_an_entry",
    ["", "  \"name\": \"second line of a response body\"", "not a date | host | main | INFO | message"],
)
def test_a_line_outside_the_team_format_is_ignored(line_that_is_not_an_entry):
    assert parse_log_line(line_that_is_not_an_entry) is None


def test_a_message_that_contains_the_separator_is_kept_whole():
    entry = parse_log_line(build_log_line("DEBUG", "GET /user -> 200 in 10 ms | auth=token | params=None"))

    assert entry.message == "GET /user -> 200 in 10 ms | auth=token | params=None"


# ----------------------------------------------------------------- RESULT lines and request lines
def test_a_passed_result_line_is_read_without_reason():
    result = parse_test_result(f"RESULT PASSED | 312 ms | {TEST_ID}")

    assert result == LoggedTestResult(outcome="PASSED", duration_ms=312, test_id=TEST_ID, reason="")


def test_a_failed_result_line_keeps_the_whole_reason_even_if_it_has_the_separator():
    result = parse_test_result(f"RESULT FAILED | 540 ms | {TEST_ID} | reason=assert 'a | b' == 'c'")

    assert result.outcome == "FAILED"
    assert result.reason == "assert 'a | b' == 'c'"


def test_a_message_that_is_not_a_result_is_not_a_test_result():
    assert parse_test_result("START tests/labels/test_labels_post.py::test_create") is None


def test_a_request_line_is_read_with_method_path_status_and_duration():
    record = parse_request_record("POST /repos/o/r/labels -> 201 in 540 ms | auth=token | params=None")

    assert record == RequestRecord(method="POST", path="/repos/o/r/labels", status_code=201, duration_ms=540)
    assert record.endpoint == "POST /repos/o/r/labels"


def test_a_business_message_is_not_a_request():
    assert parse_request_record("Label created with name qa-pm-label") is None


def test_the_module_of_a_test_is_the_folder_inside_tests():
    assert parse_test_result(f"RESULT PASSED | 1 ms | {TEST_ID}").module == "labels"
    assert parse_test_result("RESULT PASSED | 1 ms | tests/conftest.py::test_x").module == log_report.UNKNOWN_MODULE


# ----------------------------------------------------------------- numbers of the report
def build_results(*outcomes_and_modules):
    return [
        LoggedTestResult(outcome, 100, f"tests/{module}/test_x.py::test_{index}", "")
        for index, (outcome, module) in enumerate(outcomes_and_modules)
    ]


def test_outcomes_are_counted_and_the_missing_ones_are_zero():
    results = build_results(("PASSED", "labels"), ("PASSED", "gists"), ("FAILED", "gists"))

    assert count_outcomes(results) == {"PASSED": 2, "FAILED": 1, "ERROR": 0, "SKIPPED": 0}


def test_pass_rate_is_the_percentage_of_passed_tests():
    results = build_results(("PASSED", "labels"), ("FAILED", "labels"), ("SKIPPED", "labels"), ("PASSED", "labels"))

    assert pass_rate_percentage(results) == 50.0


def test_pass_rate_of_a_run_without_tests_is_zero():
    assert pass_rate_percentage([]) == 0.0


def test_results_are_grouped_by_module_in_alphabetical_order():
    results = build_results(("PASSED", "labels"), ("FAILED", "gists"), ("PASSED", "labels"))

    grouped_results = group_results_by_module(results)

    assert list(grouped_results) == ["gists", "labels"]
    assert len(grouped_results["labels"]) == 2


def test_the_slowest_requests_come_first_and_only_the_requested_number_is_kept():
    requests = [RequestRecord("GET", f"/r{duration}", 200, duration) for duration in (30, 900, 120, 450)]

    slowest = slowest_requests(requests, how_many=2)

    assert [request.duration_ms for request in slowest] == [900, 450]


# ----------------------------------------------------------------- the run summary
def test_the_summary_separates_results_requests_errors_and_warnings(tmp_path):
    log_file_path = write_log_file(
        tmp_path,
        build_log_line("INFO", "Test run started | log_level=DEBUG | log_file=x"),
        build_log_line("DEBUG", "GET /user -> 200 in 120 ms | auth=token | params=None"),
        build_log_line("WARNING", "Cleanup: label x was already deleted"),
        build_log_line("ERROR", "GET /repos failed after 30000 ms | Read timed out"),
        build_result_line("FAILED", reason="assert 403 == 200"),
        build_result_line("SKIPPED", test_id="tests/gists/test_a.py::test_b", reason="Skipped: no token"),
        build_log_line("INFO", "Test run finished | exit_status=1", second=10),
    )

    summary = summarize_run(log_report.read_log_entries(log_file_path))

    assert [result.outcome for result in summary.test_results] == ["FAILED", "SKIPPED"]
    assert len(summary.requests) == 1
    assert summary.warning_count == 1
    assert summary.error_messages == ["GET /repos failed after 30000 ms | Read timed out"]
    assert summary.exit_status == "1"


def test_a_failed_test_is_not_counted_again_as_an_error_of_the_framework(tmp_path):
    log_file_path = write_log_file(tmp_path, build_result_line("FAILED", reason="assert 403 == 200"))

    summary = summarize_run(log_report.read_log_entries(log_file_path))

    assert summary.error_messages == []


def test_the_summary_lists_the_hosts_and_workers_of_the_run(tmp_path):
    log_file_path = write_log_file(
        tmp_path,
        build_log_line("INFO", "message", worker="gw0", host="AGENT-1"),
        build_log_line("INFO", "message", worker="gw1", host="AGENT-2"),
    )

    summary = summarize_run(log_report.read_log_entries(log_file_path))

    assert summary.hosts == {"AGENT-1", "AGENT-2"}
    assert summary.workers == {"gw0", "gw1"}


def test_the_second_line_of_a_long_message_does_not_break_the_report(tmp_path):
    log_file_path = write_log_file(
        tmp_path,
        build_log_line("DEBUG", 'POST /gists -> 201 in 80 ms | response_body={"id": 1,'),
        '  "files": {}}',
        build_result_line("PASSED"),
    )

    summary = summarize_run(log_report.read_log_entries(log_file_path))

    assert len(summary.requests) == 1
    assert len(summary.test_results) == 1


# ----------------------------------------------------------------- the text of the report
def test_the_report_has_every_section_and_the_numbers_of_the_log(tmp_path):
    log_file_path = write_log_file(
        tmp_path,
        build_log_line("DEBUG", "POST /repos/o/r/labels -> 201 in 540 ms | auth=token"),
        build_result_line("PASSED", duration_ms=1002),
        build_result_line("FAILED", test_id="tests/gists/test_a.py::test_b", reason="assert 403 == 200"),
    )

    report_text = generate_report(log_file_path)

    for section_title in ("## Run", "## Totals", "## Results per module", "## Slowest requests", "## Failures"):
        assert section_title in report_text
    assert "Pass rate: 50.0%" in report_text
    assert "| gists | 1 | 0 | 1 | 0 | 0 | 100 |" in report_text
    assert "| 540 | 201 | POST /repos/o/r/labels |" in report_text
    assert "- FAILED tests/gists/test_a.py::test_b | assert 403 == 200" in report_text


def test_without_request_lines_the_report_asks_for_debug_level(tmp_path):
    log_file_path = write_log_file(tmp_path, build_result_line("PASSED"))

    assert "LOG_LEVEL=DEBUG" in generate_report(log_file_path)


def test_a_run_without_failures_says_so(tmp_path):
    log_file_path = write_log_file(tmp_path, build_result_line("PASSED"))

    assert "No failed tests." in generate_report(log_file_path)


def test_only_the_first_errors_are_listed_and_the_rest_are_counted(tmp_path):
    error_lines = [build_log_line("ERROR", f"GET /r{number} failed after 5 ms | boom") for number in range(13)]
    log_file_path = write_log_file(tmp_path, *error_lines)

    report_text = generate_report(log_file_path)

    assert "- Errors: 13" in report_text
    assert "... and 3 more in the log file" in report_text


def test_the_report_understands_what_the_real_logger_writes(tmp_path):
    """Producer and reader must agree: the lines come from the logger of the framework, not from this test."""
    log_file_path = configure_logging("DEBUG", tmp_path)
    get_logger("unit_test").debug("GET /user -> 200 in 75 ms | auth=token | params=None")
    get_logger("unit_test").warning("Cleanup: label x was already deleted")
    result = run_logging.ExecutedTestResult(outcome="PASSED", duration_ms=250, reason="")
    get_file_only_logger("unit_test").info("%s", run_logging.build_result_message(TEST_ID, result))
    shutdown_logging()

    summary = summarize_run(log_report.read_log_entries(log_file_path))

    assert summary.test_results == [LoggedTestResult("PASSED", 250, TEST_ID, "")]
    assert [request.endpoint for request in summary.requests] == ["GET /user"]
    assert summary.warning_count == 1


# ----------------------------------------------------------------- the single command
def test_the_newest_log_file_is_the_one_with_the_latest_date_in_its_name(tmp_path):
    (tmp_path / "test_run_20261121_090000.log").write_text("")
    (tmp_path / "test_run_20261122_220008.log").write_text("")
    (tmp_path / "other_file.txt").write_text("")

    assert find_newest_log_file(tmp_path).name == "test_run_20261122_220008.log"


def test_there_is_no_newest_log_file_in_an_empty_folder(tmp_path):
    assert find_newest_log_file(tmp_path) is None


def test_the_command_prints_the_report_and_saves_it_in_the_reports_folder(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    log_file_path = write_log_file(tmp_path, build_result_line("PASSED"))

    exit_code = main([str(log_file_path)])

    assert exit_code == 0
    assert "# Test run report" in capsys.readouterr().out
    saved_report = tmp_path / "reports" / "test_run_20261122_220008_report.md"
    assert saved_report.read_text(encoding="utf-8").startswith("# Test run report")


def test_the_command_without_arguments_reads_the_newest_log_of_the_log_directory(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(log_report.settings, "LOG_DIRECTORY", str(tmp_path))
    write_log_file(tmp_path, build_result_line("PASSED"))

    assert main([]) == 0
    assert LOG_FILE_NAME in capsys.readouterr().out


def test_the_command_fails_with_a_clear_message_when_there_is_no_log(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    exit_code = main([str(tmp_path / "missing.log")])

    assert exit_code == 1
    assert "No log file found" in capsys.readouterr().out
