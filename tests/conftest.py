"""Fixtures = the hooks of pytest.

Code before `yield` is the setup (precondition), code after `yield` is the teardown (postcondition).
The scope decides how often it runs: "function" (every test), "module" (once per file),
"session" (once per run). This replaces Postman's pre-request scripts and the Teardown folder.
"""
import pytest

from config import settings
from core.api_client import GitHubClient
from core.issue_helpers import cleanup_issues, close_issue, create_issue, lock_issue


def pytest_collection_modifyitems(config, items):
    """pytest hook: skip the tests that need a token when GITHUB_TOKEN is empty."""
    if settings.TOKEN:
        return
    skip = pytest.mark.skip(reason="GITHUB_TOKEN is empty in .env")
    for item in items:
        if "no_token" not in item.keywords and "poc" not in str(item.fspath):
            item.add_marker(skip)


# ----------------------------------------------------------------- clients (session scope)
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
