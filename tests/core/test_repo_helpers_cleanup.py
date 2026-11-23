"""Tests for the `delete_leftovers` helper in `core.repo_helpers`.

These tests **mock** the GitHub client so that no network request is made.
The goal is to verify the logging and the control‑flow of the helper:

1. When the initial GET request fails (status != 200) a warning is emitted and
   no DELETE calls are performed.
2. When there are no repositories matching the test prefix, the function simply
   returns without issuing any DELETE.
3. When matching repositories are found, a DELETE is performed for each and the
   appropriate log messages (warning for successful deletion, error for failure)
   are recorded.
"""

import pytest
from types import SimpleNamespace
from pathlib import Path

from core.repo_helpers import delete_leftovers, is_test_repo
from core.logger import configure_logging, shutdown_logging
from config import settings

# ---------------------------------------------------------------------------
# Helper classes
# ---------------------------------------------------------------------------

class FakeClient:
    """A minimal fake client that returns predefined responses.

    ``responses`` is a dict mapping HTTP method name ("GET", "DELETE") to a list of
    ``SimpleNamespace`` objects that will be popped on each call.
    """

    def __init__(self, responses):
        self._responses = responses
        self.calls = []  # record of (method, url, kwargs)

    def _pop(self, method):
        lst = self._responses.get(method, [])
        if lst:
            return lst.pop(0)
        # default dummy response (200 OK)
        return SimpleNamespace(status_code=200, json=lambda: [])

    def get(self, *args, **kwargs):
        self.calls.append(("GET", args, kwargs))
        return self._pop("GET")

    def delete(self, *args, **kwargs):
        self.calls.append(("DELETE", args, kwargs))
        return self._pop("DELETE")

# ---------------------------------------------------------------------------
# Utility to read the temporary log file produced by ``configure_logging``
# ---------------------------------------------------------------------------

def read_log(log_path: Path) -> str:
    shutdown_logging()
    return log_path.read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_delete_leftovers_logs_warning_when_get_fails(tmp_path):
    client = FakeClient({"GET": [SimpleNamespace(status_code=500)]})
    log_file = configure_logging("INFO", tmp_path)

    delete_leftovers(client)

    log = read_log(log_file)
    assert "Could not list the repositories to look for leftovers" in log
    # No DELETE should have been performed
    assert not any(call[0] == "DELETE" for call in client.calls)


def test_delete_leftovers_no_matching_repos(tmp_path):
    # GET returns 200 but none of the repos match the test prefix
    repos = [
        {"owner": {"login": settings.OWNER}, "name": "some-other-repo"},
        {"owner": {"login": "other"}, "name": f"{settings.TEST_REPO_PREFIX}ignored"},
    ]
    client = FakeClient({"GET": [SimpleNamespace(status_code=200, json=lambda: repos)]})
    log_file = configure_logging("INFO", tmp_path)

    delete_leftovers(client)

    log = read_log(log_file)
    # No deletion warnings should appear
    assert "Leftover repository" not in log
    # No DELETE calls performed
    assert not any(call[0] == "DELETE" for call in client.calls)


def test_delete_leftovers_deletes_matching_and_logs(tmp_path):
    # Two matching repos: one deletes successfully (204), the other fails (500)
    name1 = f"{settings.TEST_REPO_PREFIX}repo1"
    name2 = f"{settings.TEST_REPO_PREFIX}repo2"
    repos = [
        {"owner": {"login": settings.OWNER}, "name": name1},
        {"owner": {"login": settings.OWNER}, "name": name2},
    ]
    client = FakeClient({
        "GET": [SimpleNamespace(status_code=200, json=lambda: repos)],
        "DELETE": [
            SimpleNamespace(status_code=204),  # success for repo1
            SimpleNamespace(status_code=500),  # failure for repo2
        ],
    })
    log_file = configure_logging("INFO", tmp_path)

    delete_leftovers(client)

    log = read_log(log_file)
    # Successful deletion is logged as a warning (per original implementation)
    assert f"Leftover repository from a previous run deleted: {name1}" in log
    # Failure is logged as an error
    assert f"Could not delete the leftover repository {name2} | status=500" in log
    # Verify that two DELETE calls were made with the correct endpoints
    delete_calls = [c for c in client.calls if c[0] == "DELETE"]
    assert len(delete_calls) == 2
    assert name1 in delete_calls[0][1][0]
    assert name2 in delete_calls[1][1][0]

# ---------------------------------------------------------------------------
# Sanity checks for the `is_test_repo` helper (used by other code)
# ---------------------------------------------------------------------------

def test_is_test_repo_true_for_correct_prefix():
    repo_name = f"{settings.TEST_REPO_PREFIX}example"
    assert is_test_repo(repo_name)


def test_is_test_repo_false_for_wrong_prefix():
    assert not is_test_repo("random-repo")
