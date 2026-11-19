"""PATCH /repos/{owner}/{repo} (folder 03_PATCH_Update_Repo of the Postman collection).

PATCH_005 targets a non-existent repository and needs no precondition.

PATCH_001 through PATCH_004, PATCH_006 and PATCH_007 each receive a fresh repository
through the patch_repo fixture (function scope). Each test is fully independent.
"""
import time

import pytest

from config import settings
from config.settings import Endpoints
from core import data_factory
from core.assertions import assert_common, assert_error, assert_schema
from core.schemas import ERROR_SCHEMA, REPO_SCHEMA


# ----------------------------------------------------------------- PATCH_001: update description only
def test_tc_repo_patch_001_verify_that_only_the_description_changes_when_patching_description(github, patch_repo):
    name = patch_repo["name"]
    response = github.patch(Endpoints.repository(name), json={"description": "Updated description via API"})

    assert response.status_code == 200
    assert_common(response)
    repo = response.json()
    assert repo["description"] == "Updated description via API"
    assert repo["name"] == name       # name must not have changed
    assert repo["visibility"] == "public"  # visibility must not have changed
    assert_schema(repo, REPO_SCHEMA)


# ----------------------------------------------------------------- PATCH_002: updated_at advances after PATCH
def test_tc_repo_patch_002_verify_that_updated_at_advances_after_a_patch(github, patch_repo):
    name = patch_repo["name"]

    # GET the baseline updated_at before modifying the repository.
    get_response = github.get(Endpoints.repository(name))
    assert get_response.status_code == 200
    updated_at_before = get_response.json()["updated_at"]

    # Wait so GitHub's one-second-precision timestamp is guaranteed to advance.
    # time.sleep(2) is synchronous and always waits the full duration before the PATCH fires,
    # unlike Postman's setTimeout which does not block the request thread.
    time.sleep(2)

    response = github.patch(
        Endpoints.repository(name),
        json={"description": "Description for updated_at comparison"},
    )

    assert response.status_code == 200
    assert_common(response)
    updated_at_after = response.json()["updated_at"]
    # Both values are ISO 8601 UTC strings (YYYY-MM-DDTHH:MM:SSZ); lexicographic comparison is valid.
    assert updated_at_after > updated_at_before, (
        f"updated_at did not advance: before={updated_at_before}, after={updated_at_after}"
    )


# ----------------------------------------------------------------- PATCH_003: description persists after a GET
def test_tc_repo_patch_003_verify_that_the_description_persists_after_a_get(github, patch_repo):
    name = patch_repo["name"]
    response = github.patch(
        Endpoints.repository(name),
        json={"description": "Persisted via PATCH and GET"},
    )

    assert response.status_code == 200
    assert_common(response)
    # Integrity: a subsequent GET must return the description that was just set
    get_response = github.get(Endpoints.repository(name))
    assert get_response.status_code == 200
    assert_common(get_response)
    assert get_response.json()["description"] == "Persisted via PATCH and GET"


# ----------------------------------------------------------------- PATCH_004: rename makes repo available under new name
def test_tc_repo_patch_004_verify_that_renaming_a_repo_makes_it_available_under_the_new_name(github, patch_repo):
    original_name = patch_repo["name"]
    new_name = data_factory.repo_name("TC_REPO_PATCH_004_RENAMED")
    # Register the new name so the fixture teardown can delete the renamed repository.
    # cleanup_repos accepts 404 for the original name (it no longer exists after rename).
    patch_repo["extra_names"].append(new_name)

    response = github.patch(Endpoints.repository(original_name), json={"name": new_name})

    assert response.status_code == 200
    assert_common(response)
    assert response.json()["name"] == new_name
    assert_schema(response.json(), REPO_SCHEMA)
    # Integrity: the repository must be accessible under the new name
    get_response = github.get(Endpoints.repository(new_name))
    assert get_response.status_code == 200
    assert_common(get_response)
    assert get_response.json()["full_name"] == f"{settings.OWNER}/{new_name}"


# ----------------------------------------------------------------- PATCH_005: non-existent repo returns 404
@pytest.mark.negative
def test_tc_repo_patch_005_verify_that_patching_a_non_existent_repo_returns_404(github):
    response = github.patch(Endpoints.repository(settings.NON_EXISTENT_REPO), json={"description": "testing non-existent repo"})

    assert_error(response, 404, "Not Found")


# ----------------------------------------------------------------- PATCH_006: 403 without admin permission
@pytest.mark.negative
def test_tc_repo_patch_006_verify_that_patch_with_a_token_without_admin_permission_returns_403(no_admin_client, patch_repo):
    # patch_repo is created with github (which has admin access).
    # The PATCH is sent with no_admin_client (tokenNoAdmin), which lacks Administration write permission.
    name = patch_repo["name"]
    response = no_admin_client.patch(
        Endpoints.repository(name),
        json={"description": "Should not be updated - no admin permission"},
    )

    assert response.status_code == 403
    assert_common(response)
    assert isinstance(response.json()["message"], str) and response.json()["message"] != ""
    assert_schema(response.json(), ERROR_SCHEMA)


# ----------------------------------------------------------------- PATCH_007: invalid visibility is rejected (known discrepancy)
@pytest.mark.negative
def test_tc_repo_patch_007_verify_that_an_invalid_visibility_is_rejected_and_the_repo_is_not_changed(github, patch_repo):
    name = patch_repo["name"]

    # Step 1: execute PATCH with an invalid visibility value.
    patch_response = github.patch(Endpoints.repository(name), json={"visibility": "secret"})

    # Step 2: execute GET to verify the repository state before asserting either response.
    # This ensures both API calls are made regardless of what the PATCH returned.
    get_response = github.get(Endpoints.repository(name))

    # Step 3: assert PATCH response.
    # Finding (Newman run): GitHub returned 200 instead of 422 for visibility='secret'.
    # The original Postman assertion is preserved to document the discrepancy.
    # Do not change this assertion to make the test pass.
    assert patch_response.status_code == 422
    assert patch_response.json()["message"] == "Validation Failed"
    assert_common(patch_response)

    # Step 3 (continued): assert GET response — visibility must remain unchanged.
    assert get_response.status_code == 200
    assert get_response.json()["visibility"] == "public"
    assert_common(get_response)
