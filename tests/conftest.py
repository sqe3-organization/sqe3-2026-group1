"""Fixtures = the hooks of pytest.

Code before `yield` is the setup (precondition), code after `yield` is the teardown (postcondition).
The scope decides how often it runs: "function" (every test), "module" (once per file),
"session" (once per run). This replaces Postman's pre-request scripts and the Teardown folder.
"""
from pathlib import Path

import pytest

from config import settings
from core.api_client import GitHubClient
from core.logger import get_current_log_file, get_file_only_logger
from core.request_manager import RequestManager
from core.issue_helpers import cleanup_issues, close_issue, create_issue, lock_issue
from core.run_logging import LOG_LEVEL_BY_OUTCOME, build_result_message, summarize_test_result

logger = get_file_only_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
reports_by_test = {}  # test id -> {phase: pytest report}, until the teardown phase finishes


def pytest_collection_modifyitems(config, items):
    """pytest hook: skip the tests that need a token when GITHUB_TOKEN is empty."""
    if settings.TOKEN:
        return
    skip = pytest.mark.skip(reason="GITHUB_TOKEN is empty in .env")
    for item in items:
        if "no_token" not in item.keywords and "poc" not in str(item.fspath):
            item.add_marker(skip)


# ----------------------------------------------------------------- logging hooks
def is_fixture_of_this_project(fixturedef):
    """Fixtures of pytest and of its plugins (tmp_path, capsys, faker...) are not logged."""
    fixture_file = Path(fixturedef.func.__code__.co_filename).resolve()
    return PROJECT_ROOT in fixture_file.parents


def pytest_sessionstart():
    """pytest hook: first line of the log of the run."""
    logger.info("Test run started | log_level=%s | log_file=%s", settings.LOG_LEVEL, get_current_log_file())


def pytest_sessionfinish(exitstatus):
    """pytest hook: last line of the log of the run."""
    logger.info("Test run finished | exit_status=%s", int(exitstatus))


def pytest_terminal_summary(terminalreporter):
    """pytest hook: tells where the log of the run was written."""
    terminalreporter.write_line(f"Log file of this run: {get_current_log_file()}")


@pytest.hookimpl(wrapper=True)
def pytest_fixture_setup(fixturedef):
    """pytest hook: logs the setup (precondition) of every fixture of this project."""
    if is_fixture_of_this_project(fixturedef):
        logger.debug("Fixture setup: %s (scope=%s)", fixturedef.argname, fixturedef.scope)
    return (yield)


def pytest_fixture_post_finalizer(fixturedef):
    """pytest hook: logs the cleanup (postcondition) of every fixture of this project."""
    if is_fixture_of_this_project(fixturedef):
        logger.debug("Fixture cleanup: %s (scope=%s)", fixturedef.argname, fixturedef.scope)


def pytest_runtest_logstart(nodeid):
    """pytest hook: a test is about to start."""
    logger.info("START %s", nodeid)


def pytest_runtest_logreport(report):
    """pytest hook: collects the reports of the three phases and logs the result of the test
    once its teardown has finished."""
    reports_by_phase = reports_by_test.setdefault(report.nodeid, {})
    reports_by_phase[report.when] = report
    if report.when != "teardown":
        return
    result = summarize_test_result(reports_by_test.pop(report.nodeid))
    logger.log(LOG_LEVEL_BY_OUTCOME[result.outcome], "%s", build_result_message(report.nodeid, result))


# ----------------------------------------------------------------- request manager (Singleton)
@pytest.fixture(scope="session", autouse=True)
def request_manager():
    """[Pre and Cleanup] The only RequestManager of the run: every client below shares its session.
    Its connections are closed once, after the last test."""
    manager = RequestManager.get_instance()
    yield manager
    RequestManager.reset()


# ----------------------------------------------------------------- clients (session scope)
# Each client is one identity (token); all of them send through the same RequestManager.
@pytest.fixture(scope="session")
def github():
    return GitHubClient()


@pytest.fixture(scope="session")
def anonymous():
    return GitHubClient(token=None)


@pytest.fixture(scope="session")
def invalid_client():
    return GitHubClient(token=settings.INVALID_TOKEN)


# ----------------------------------------------------------------- cleanup only
@pytest.fixture
def created_issues(github):
    """[Cleanup] The test appends the numbers it creates; they are closed afterwards,
    even when the test fails."""
    numbers = []
    yield numbers
    cleanup_issues(github, numbers)


# ----------------------------------------------------------------- pre + cleanup
@pytest.fixture
def open_issue(github, request):
    """[Pre and Cleanup] A fresh open issue for each test."""
    tc_id = request.node.name.split("_verify")[0].replace("test_", "").upper()
    issue = create_issue(github, tc_id)
    yield issue
    cleanup_issues(github, [issue["number"]])


@pytest.fixture
def closed_issue(github, open_issue):
    """[Pre] Builds on open_issue (fixtures can depend on other fixtures)."""
    return close_issue(github, open_issue["number"])


@pytest.fixture
def locked_issue(github, open_issue):
    lock_issue(github, open_issue["number"])
    return open_issue