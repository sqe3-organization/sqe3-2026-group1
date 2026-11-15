"""E2E flows (folders 05 and 06 of the Postman collection)."""
import pytest

from config.settings import Endpoints
from core import data_factory
from core.assertions import assert_schema
from core.issue_helpers import wait_until
from core.schemas import ISSUE_SCHEMA


def _open_numbers(github):
    return [i["number"] for i in github.get(Endpoints.ISSUES, params={"state": "open", "per_page": 100}).json()]


@pytest.mark.e2e
def test_tc_iss_e2e_001_verify_the_full_lifecycle_of_an_issue(github, created_issues):
    """In Postman this was a folder of 10 chained requests; here the steps share local variables."""
    title = data_factory.issue_title("TC_ISS_E2E_001")

    # Step 01 - create
    created = github.post(Endpoints.ISSUES, json={"title": title})
    assert created.status_code == 201
    number = created.json()["number"]
    created_issues.append(number)

    # Step 02 - read it
    read = github.get(Endpoints.issue(number))
    assert read.status_code == 200
    assert (read.json()["title"], read.json()["state"]) == (title, "open")

    # Step 03 - update the title
    title = f"{title} (updated)"
    updated = github.patch(Endpoints.issue(number), json={"title": title})
    assert updated.status_code == 200
    assert updated.json()["title"] == title

    # Step 04 - it appears in the open list (eventually consistent, so retry)
    assert wait_until(lambda: number in _open_numbers(github)), "issue not found in the open list"

    # Step 05 - close as completed
    closed = github.patch(Endpoints.issue(number), json={"state": "closed", "state_reason": "completed"})
    assert closed.status_code == 200
    assert (closed.json()["state"], closed.json()["state_reason"]) == ("closed", "completed")

    # Step 06 - it leaves the open list
    assert wait_until(lambda: number not in _open_numbers(github)), "closed issue still in the open list"

    # Step 07 - reopen
    reopened = github.patch(Endpoints.issue(number), json={"state": "open"})
    assert reopened.status_code == 200
    assert (reopened.json()["state"], reopened.json()["state_reason"]) == ("open", "reopened")

    # Step 08 - lock / Step 09 - unlock
    assert github.put(Endpoints.issue_lock(number), json={"lock_reason": "resolved"}).status_code == 204
    assert github.delete(Endpoints.issue_lock(number)).status_code == 204

    # Step 10 - final state
    final = github.get(Endpoints.issue(number))
    assert final.status_code == 200
    assert final.json()["state"] == "open"
    assert final.json()["locked"] is False
    assert final.json()["title"] == title
    assert_schema(final.json(), ISSUE_SCHEMA)


@pytest.mark.e2e
@pytest.mark.negative
def test_tc_iss_e2e_002_verify_that_the_token_cannot_write_issues_on_another_repository(github):
    """The fine-grained token only has access to the test repository."""
    foreign = Endpoints.PUBLIC_ISSUES

    assert github.post(foreign, json={"title": "TC_ISS_E2E_002 - must not be created"}).status_code in (403, 404)
    assert github.patch(f"{foreign}/1", json={"title": "TC_ISS_E2E_002 - must not be applied"}).status_code in (403, 404)
    assert github.put(f"{foreign}/1/lock", json={"lock_reason": "spam"}).status_code in (403, 404)

    # data integrity: issue #1 of the public repository did not change
    issue = github.get(f"{foreign}/1")
    assert issue.status_code == 200
    assert "TC_ISS_E2E_002" not in issue.json()["title"]
