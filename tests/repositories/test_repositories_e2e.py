"""End-to-end flows (folder 05_E2E of the Postman collection).

Each test covers a complete lifecycle in a single function with local variables carrying
state between steps, replacing the collection variables of Postman.

E2E_001 (githubToken):
    POST → GET → PATCH → GET → DELETE → GET
    The repository is deleted during the test (Step 5); the repo_names_to_clean_up
    teardown will receive a 404 for it, which cleanup_repos accepts.

E2E_002 (tokenRepoOnly for Steps 1-3, githubToken for Step 4):
    POST → PATCH → DELETE (rejected 403) → GET
    The repository is NOT deleted during the test; teardown removes it via github.
    If TOKEN_REPO_ONLY is not set in .env, this test is skipped automatically.
"""
import pytest

from config.settings import Endpoints
from core import data_factory
from core.assertions import assert_common


# ----------------------------------------------------------------- E2E_001: full lifecycle
@pytest.mark.e2e
def test_tc_repo_e2e_001_full_repository_lifecycle(github, repo_names_to_clean_up):
    name = data_factory.repo_name("TC_REPO_E2E_001")
    repo_names_to_clean_up.append(name)  # safety net: accepts 404 if Step 5 already deleted it

    # Step 1: POST — create the repository
    post_response = github.post(
        Endpoints.USER_REPOS,
        json={"name": name, "description": "E2E lifecycle test repo", "private": False},
    )
    assert post_response.status_code == 201
    assert_common(post_response)

    # Step 2: GET — the repository is reachable immediately after creation
    get_response = github.get(Endpoints.repository(name))
    assert get_response.status_code == 200
    assert_common(get_response)

    # Step 3: PATCH — update the description
    patch_response = github.patch(
        Endpoints.repository(name),
        json={"description": "Updated via E2E lifecycle test"},
    )
    assert patch_response.status_code == 200
    assert_common(patch_response)
    assert patch_response.json()["description"] == "Updated via E2E lifecycle test"

    # Step 4: GET — the updated description is persisted
    get2_response = github.get(Endpoints.repository(name))
    assert get2_response.status_code == 200
    assert_common(get2_response)
    assert get2_response.json()["description"] == "Updated via E2E lifecycle test"

    # Step 5: DELETE — remove the repository
    del_response = github.delete(Endpoints.repository(name))
    assert del_response.status_code == 204

    # Step 6: GET — the deleted repository returns 404
    get3_response = github.get(Endpoints.repository(name))
    assert get3_response.status_code == 404


# ----------------------------------------------------------------- E2E_002: token with repo scope but without delete_repo
@pytest.mark.e2e
def test_tc_repo_e2e_002_token_with_repo_scope_but_without_delete_repo(github, repo_only_client, repo_names_to_clean_up):
    # repo_only_client skips automatically if TOKEN_REPO_ONLY is empty in .env.
    # Steps 1-3 use repo_only_client (tokenRepoOnly: has repo scope, no delete_repo).
    # Step 4 uses github (githubToken) to verify the repository is still accessible.
    name = data_factory.repo_name("TC_REPO_E2E_002")
    repo_names_to_clean_up.append(name)  # repository is not deleted by the test; teardown removes it

    # Step 1: POST with tokenRepoOnly — create the repository
    post_response = repo_only_client.post(
        Endpoints.USER_REPOS,
        json={"name": name, "description": "E2E_002 test repo", "private": False},
    )
    assert post_response.status_code == 201
    assert_common(post_response)

    # Step 2: PATCH with tokenRepoOnly — update the description
    patch_response = repo_only_client.patch(
        Endpoints.repository(name),
        json={"description": "Updated via E2E_002"},
    )
    assert patch_response.status_code == 200
    assert_common(patch_response)
    assert patch_response.json()["description"] == "Updated via E2E_002"

    # Step 3: DELETE with tokenRepoOnly — expects 403 (no delete_repo scope)
    del_response = repo_only_client.delete(Endpoints.repository(name))
    assert del_response.status_code == 403
    assert_common(del_response)
    assert "admin rights" in del_response.json()["message"]

    # Step 4: GET with githubToken — repository still exists and description from Step 2 is present
    get_response = github.get(Endpoints.repository(name))
    assert get_response.status_code == 200
    assert_common(get_response)
    assert get_response.json()["description"] == "Updated via E2E_002"
