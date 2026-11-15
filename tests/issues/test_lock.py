"""PUT/DELETE /repos/{owner}/{repo}/issues/{issue_number}/lock (folder 04 of the Postman collection).

In Postman LOCK_002 depended on LOCK_001. Here the locked_issue fixture leaves the issue locked."""
import json

import pytest

from config import settings
from config.settings import Endpoints
from core.assertions import assert_common, assert_error


@pytest.mark.smoke
def test_tc_iss_lock_001_verify_that_an_issue_can_be_locked_with_a_valid_reason(github, open_issue):
    response = github.put(Endpoints.issue_lock(open_issue["number"]), json={"lock_reason": "too heated"})

    assert response.status_code == 204
    assert_common(response)
    assert response.text == ""
    # data integrity
    saved = github.get(Endpoints.issue(open_issue["number"])).json()
    assert saved["locked"] is True
    assert saved["active_lock_reason"] == "too heated"


def test_tc_iss_lock_002_verify_that_a_locked_issue_can_be_unlocked(github, locked_issue):
    response = github.delete(Endpoints.issue_lock(locked_issue["number"]))

    assert response.status_code == 204
    assert_common(response)
    saved = github.get(Endpoints.issue(locked_issue["number"])).json()
    assert saved["locked"] is False
    assert saved["active_lock_reason"] is None


@pytest.mark.negative
def test_tc_iss_lock_003_verify_that_an_invalid_lock_reason_is_rejected(github, open_issue):
    response = github.put(Endpoints.issue_lock(open_issue["number"]), json={"lock_reason": "boring"})

    assert response.status_code == 422
    assert_common(response)
    text = json.dumps(response.json())
    for reason in settings.LOCK_REASONS:
        assert reason in text
    assert github.get(Endpoints.issue(open_issue["number"])).json()["locked"] is False


@pytest.mark.negative
def test_tc_iss_lock_004_verify_that_an_issue_cannot_be_locked_with_an_invalid_token(github, invalid_client, open_issue):
    response = invalid_client.put(Endpoints.issue_lock(open_issue["number"]), json={"lock_reason": "spam"})

    assert_error(response, 401, "Bad credentials")
    assert github.get(Endpoints.issue(open_issue["number"])).json()["locked"] is False
