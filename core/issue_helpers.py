"""Pre and postconditions used by the fixtures in tests/conftest.py.

They replace the pre-request scripts and the "99 - Teardown" folder of the Postman collection.
"""
import time

from config.settings import Endpoints
from core import data_factory


def create_issue(client, tc_id, **extra):
    response = client.post(Endpoints.ISSUES, json={"title": data_factory.issue_title(tc_id), **extra})
    assert response.status_code == 201, f"Precondition failed: could not create the issue ({response.status_code})"
    return response.json()


def close_issue(client, number, reason="completed"):
    response = client.patch(Endpoints.issue(number), json={"state": "closed", "state_reason": reason})
    assert response.status_code == 200, f"Precondition failed: could not close #{number} ({response.status_code})"
    return response.json()


def lock_issue(client, number, reason="resolved"):
    response = client.put(Endpoints.issue_lock(number), json={"lock_reason": reason})
    assert response.status_code == 204, f"Precondition failed: could not lock #{number} ({response.status_code})"


def cleanup_issues(client, numbers):
    """GitHub does not allow deleting issues through REST, so cleanup closes them as not_planned.
    It does not raise: a failed cleanup must not hide the real result of the test."""
    for number in numbers:
        response = client.patch(Endpoints.issue(number), json={"state": "closed", "state_reason": "not_planned"})
        if response.status_code != 200:
            print(f"[Cleanup] Could not close issue #{number}: {response.status_code}")
    numbers.clear()


def wait_until(condition, timeout=15, interval=1):
    """Retries a check until it returns True. The issues list is eventually consistent (Lab 1 finding)."""
    deadline = time.monotonic() + timeout
    while True:
        result = condition()
        if result or time.monotonic() > deadline:
            return result
        time.sleep(interval)
