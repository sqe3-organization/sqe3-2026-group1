
"""Report of one test run, built from its log file (no new dependency).

Single command (it reads the newest log of LOG_DIRECTORY, or the file you give):

    python -m core.log_report
    python -m core.log_report logs/test_run_20261122_220008.log

It prints the report and also saves it as Markdown in the reports/ folder (ignored by git).

The report reads three kinds of lines written by the framework:
- RESULT lines (core/run_logging.py): one per test, always written at INFO level or above.
- Request lines of the RequestManager: "GET /path -> 200 in 120 ms". They are written at DEBUG level,
  so the section of slowest requests is empty unless the run used LOG_LEVEL=DEBUG.
- ERROR lines: failed requests and failed cleanups.
Lines that do not start with the team format (for example the second line of a long message) are ignored.
"""
import argparse
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from config import settings
from core import run_logging
from core.logger import LOG_FIELD_SEPARATOR, LOG_FILE_NAME_TEMPLATE

REPORTS_DIRECTORY = "reports"
LOG_FILE_SEARCH_PATTERN = LOG_FILE_NAME_TEMPLATE.format(run_id="*")
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S,%f"
NUMBER_OF_LOG_FIELDS = 5

REQUEST_LINE_PATTERN = re.compile(
    r"^(?P<method>[A-Z]+) (?P<path>\S+) -> (?P<status_code>\d+) in (?P<duration_ms>\d+) ms"
)
RUN_FINISHED_PREFIX = "Test run finished | exit_status="

UNKNOWN_MODULE = "other"
NUMBER_OF_SLOWEST_REQUESTS = 5
MAX_ERRORS_LISTED = 10
OUTCOMES_IN_REPORT_ORDER = (run_logging.PASSED, run_logging.FAILED, run_logging.ERROR, run_logging.SKIPPED)
OUTCOMES_THAT_NEED_ATTENTION = (run_logging.FAILED, run_logging.ERROR)


@dataclass(frozen=True)
class LogEntry:
    """One line of the log file, split in the fields of the team format."""

    timestamp: datetime
    host: str
    worker: str
    level: str
    message: str


@dataclass(frozen=True)
class LoggedTestResult:
    outcome: str
    duration_ms: int
    test_id: str
    reason: str

    @property
    def module(self):
        """tests/issues/test_post.py::test_create -> issues"""
        path_parts = self.test_id.split("::")[0].split("/")
        return path_parts[1] if len(path_parts) > 2 else UNKNOWN_MODULE


@dataclass(frozen=True)
class RequestRecord:
    method: str
    path: str
    status_code: int
    duration_ms: int

    @property
    def endpoint(self):
        return f"{self.method} {self.path}"


@dataclass
class RunSummary:
    """Everything the report shows, already extracted from the log."""

    started_at: datetime = None
    finished_at: datetime = None
    exit_status: str = "unknown"
    hosts: set = field(default_factory=set)
    workers: set = field(default_factory=set)
    test_results: list = field(default_factory=list)
    requests: list = field(default_factory=list)
    error_messages: list = field(default_factory=list)
    warning_count: int = 0


def parse_log_line(line):
    """Returns the LogEntry of a line, or None when the line does not follow the team format."""
    fields = line.rstrip("\n").split(LOG_FIELD_SEPARATOR, NUMBER_OF_LOG_FIELDS - 1)
    if len(fields) != NUMBER_OF_LOG_FIELDS:
        return None
    timestamp_text, host, worker, level, message = fields
    try:
        timestamp = datetime.strptime(timestamp_text, TIMESTAMP_FORMAT)
    except ValueError:
        return None
    return LogEntry(timestamp, host, worker, level.strip(), message)


def read_log_entries(log_file_path):
    with open(log_file_path, encoding="utf-8") as log_file:
        parsed_lines = (parse_log_line(line) for line in log_file)
        return [entry for entry in parsed_lines if entry is not None]


def parse_test_result(message):
    """Returns the LoggedTestResult of a RESULT line, or None when the message is another kind of line."""
    if not message.startswith(run_logging.RESULT_LINE_PREFIX + " "):
        return None
    result_field, duration_field, test_id, *reason_field = message.split(run_logging.RESULT_FIELD_SEPARATOR, 3)
    outcome = result_field.removeprefix(run_logging.RESULT_LINE_PREFIX + " ")
    reason = reason_field[0].removeprefix(run_logging.REASON_FIELD_PREFIX) if reason_field else ""
    return LoggedTestResult(outcome, int(duration_field.removesuffix(" ms")), test_id, reason)


def parse_request_record(message):
    """Returns the RequestRecord of a request line of the RequestManager, or None."""
    match = REQUEST_LINE_PATTERN.match(message)
    if match is None:
        return None
    return RequestRecord(
        method=match["method"],
        path=match["path"],
        status_code=int(match["status_code"]),
        duration_ms=int(match["duration_ms"]),
    )


def summarize_run(entries):
    summary = RunSummary()
    for entry in entries:
        summary.started_at = summary.started_at or entry.timestamp
        summary.finished_at = entry.timestamp
        summary.hosts.add(entry.host)
        summary.workers.add(entry.worker)

        test_result = parse_test_result(entry.message)
        request_record = parse_request_record(entry.message)
        if test_result:
            summary.test_results.append(test_result)
        elif request_record:
            summary.requests.append(request_record)
        elif entry.message.startswith(RUN_FINISHED_PREFIX):
            summary.exit_status = entry.message.removeprefix(RUN_FINISHED_PREFIX)
        elif entry.level == "ERROR":
            summary.error_messages.append(entry.message)
        elif entry.level == "WARNING":
            summary.warning_count += 1
    return summary


def count_outcomes(test_results):
    outcome_counts = Counter(result.outcome for result in test_results)
    return {outcome: outcome_counts[outcome] for outcome in OUTCOMES_IN_REPORT_ORDER}


def group_results_by_module(test_results):
    results_by_module = defaultdict(list)
    for result in test_results:
        results_by_module[result.module].append(result)
    return dict(sorted(results_by_module.items()))


def pass_rate_percentage(test_results):
    if not test_results:
        return 0.0
    passed_tests = sum(1 for result in test_results if result.outcome == run_logging.PASSED)
    return 100 * passed_tests / len(test_results)


def slowest_requests(requests, how_many=NUMBER_OF_SLOWEST_REQUESTS):
    return sorted(requests, key=lambda request: request.duration_ms, reverse=True)[:how_many]


def render_markdown_table(header, rows):
    table_lines = [
        "| " + " | ".join(header) + " |",
        "|" + "|".join(" --- " for _ in header) + "|",
    ]
    table_lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join(table_lines)


def render_run_section(summary, log_file_name):
    duration = summary.finished_at - summary.started_at if summary.started_at else "unknown"
    return "\n".join([
        "## Run",
        f"- Log file: {log_file_name}",
        f"- Started at: {summary.started_at} | duration: {duration}",
        f"- Exit status of pytest: {summary.exit_status}",
        f"- Hosts: {', '.join(sorted(summary.hosts))} | workers: {', '.join(sorted(summary.workers))}",
    ])


def render_totals_section(test_results):
    outcome_counts = count_outcomes(test_results)
    rows = [[outcome, count] for outcome, count in outcome_counts.items()]
    rows.append(["TOTAL", len(test_results)])
    return "\n".join([
        "## Totals",
        render_markdown_table(["Outcome", "Tests"], rows),
        "",
        f"Pass rate: {pass_rate_percentage(test_results):.1f}%",
    ])


def render_modules_section(test_results):
    rows = []
    for module, module_results in group_results_by_module(test_results).items():
        outcome_counts = count_outcomes(module_results)
        total_duration_ms = sum(result.duration_ms for result in module_results)
        rows.append([module, len(module_results), *outcome_counts.values(), total_duration_ms])
    header = ["Module", "Tests", *OUTCOMES_IN_REPORT_ORDER, "Time (ms)"]
    return "\n".join(["## Results per module", render_markdown_table(header, rows)])


def render_slowest_requests_section(requests):
    if not requests:
        return (
            "## Slowest requests\n"
            "No request lines in this log. Run the tests with LOG_LEVEL=DEBUG to record them."
        )
    rows = [[request.duration_ms, request.status_code, request.endpoint] for request in slowest_requests(requests)]
    return "\n".join([
        f"## Slowest requests (of {len(requests)})",
        render_markdown_table(["Time (ms)", "Status", "Request"], rows),
    ])


def render_failures_section(summary):
    tests_that_need_attention = [
        result for result in summary.test_results if result.outcome in OUTCOMES_THAT_NEED_ATTENTION
    ]
    if not tests_that_need_attention:
        return "## Failures\nNo failed tests."
    lines = ["## Failures"]
    lines += [f"- {result.outcome} {result.test_id} | {result.reason}" for result in tests_that_need_attention]
    return "\n".join(lines)


def render_errors_section(summary):
    lines = [
        "## Errors and warnings of the framework",
        f"- Warnings: {summary.warning_count}",
        f"- Errors: {len(summary.error_messages)}",
    ]
    lines += [f"  - {message}" for message in summary.error_messages[:MAX_ERRORS_LISTED]]
    hidden_errors = len(summary.error_messages) - MAX_ERRORS_LISTED
    if hidden_errors > 0:
        lines.append(f"  - ... and {hidden_errors} more in the log file")
    return "\n".join(lines)


def render_report(summary, log_file_name):
    sections = [
        render_run_section(summary, log_file_name),
        render_totals_section(summary.test_results),
        render_modules_section(summary.test_results),
        render_slowest_requests_section(summary.requests),
        render_failures_section(summary),
        render_errors_section(summary),
    ]
    return "# Test run report\n\n" + "\n\n".join(sections) + "\n"


def find_newest_log_file(log_directory):
    """The names of the log files start with the date of the run, so the last one by name is the newest."""
    log_files = sorted(Path(log_directory).glob(LOG_FILE_SEARCH_PATTERN))
    return log_files[-1] if log_files else None


def save_report(report_text, log_file_path, reports_directory=REPORTS_DIRECTORY):
    Path(reports_directory).mkdir(parents=True, exist_ok=True)
    report_path = Path(reports_directory) / f"{log_file_path.stem}_report.md"
    report_path.write_text(report_text, encoding="utf-8")
    return report_path


def generate_report(log_file_path):
    """Reads a log file and returns the text of its report."""
    summary = summarize_run(read_log_entries(log_file_path))
    return render_report(summary, Path(log_file_path).name)


def main(arguments=None):
    parser = argparse.ArgumentParser(description="Report of a test run, built from its log file.")
    parser.add_argument("log_file", nargs="?", help="log file to read (default: the newest one of LOG_DIRECTORY)")
    given_arguments = parser.parse_args(arguments)

    if given_arguments.log_file:
        log_file_path = Path(given_arguments.log_file)
    else:
        log_file_path = find_newest_log_file(settings.LOG_DIRECTORY)
    if log_file_path is None or not log_file_path.is_file():
        print(f"No log file found. Run the tests first (logs are written to '{settings.LOG_DIRECTORY}').")
        return 1

    report_text = generate_report(log_file_path)
    report_path = save_report(report_text, log_file_path)
    print(report_text)
    print(f"Report saved in {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
