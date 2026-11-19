"""DELETE /repos/{owner}/{repo} (folder 04_DELETE_Delete_Repo of the Postman collection).

DELETE_004 targets a non-existent repository and needs no precondition.

DELETE_001, DELETE_002 and DELETE_003 each receive a fresh repository through the
delete_target_repo fixture (function scope). Every test is fully independent.

Design note — DELETE_003:
In the Postman collection DELETE_003 reused the repository created by POST_001, relying on
the fixed execution order of the collection runner. In pytest, test order is not guaranteed,
so DELETE_003 receives its own repository via delete_target_repo. The expected behaviour
(403 + repo unchanged) is identical; only the precondition strategy changes.
"""
import pytest

from config import settings
from config.settings import Endpoints
from core.assertions import assert_common, assert_error, assert_no_content, assert_schema
from core.schemas import ERROR_SCHEMA


# ----------------------------------------------------------------- DELETE_001: 204 and body empty
def test_tc_repo_delete_001_verify_that_deleting_a_repo_with_delete_repo_scope_returns_204(github, delete_target_repo):
    response = github.delete(Endpoints.repository(delete_target_repo))

    assert_no_content(response)  # 204 + empty body + common headers
    # Integrity: a GET immediately after deletion must return 404
    get_response = github.get(Endpoints.repository(delete_target_repo))
    assert get_response.status_code == 404


# ----------------------------------------------------------------- DELETE_002: deleted repo returns 404 on GET
def test_tc_repo_delete_002_verify_that_the_deleted_repo_returns_404_on_get(github, delete_target_repo):
    # This test focuses on verifying the GET response after deletion.
    del_response = github.delete(Endpoints.repository(delete_target_repo))
    assert del_response.status_code == 204

    response = github.get(Endpoints.repository(delete_target_repo))

    assert_error(response, 404, "Not Found")


# ----------------------------------------------------------------- DELETE_003: 403 without delete_repo scope
@pytest.mark.negative
def test_tc_repo_delete_003_verify_that_delete_without_delete_repo_scope_returns_403_and_the_repo_is_unchanged(
    github, repo_only_client, delete_target_repo
):
    # Design note: in Postman this test reused repoName_POST001 (created by POST_001).
    # In pytest each test is independent, so delete_target_repo creates a dedicated repository.
    # The expected behaviour is identical: tokenRepoOnly (repo scope, no delete_repo) must be
    # rejected with 403 and the repository must still exist afterwards.
    response = repo_only_client.delete(Endpoints.repository(delete_target_repo))

    assert response.status_code == 403
    assert_common(response)
    assert "admin rights" in response.json()["message"]
    assert_schema(response.json(), ERROR_SCHEMA)
    # Integrity: the repository must still exist after the rejected DELETE
    get_response = github.get(Endpoints.repository(delete_target_repo))
    assert get_response.status_code == 200


# ----------------------------------------------------------------- DELETE_004: non-existent repo returns 404
@pytest.mark.negative
def test_tc_repo_delete_004_verify_that_deleting_a_non_existent_repo_returns_404(github):
    response = github.delete(Endpoints.repository(settings.NON_EXISTENT_REPO))

    assert_error(response, 404, "Not Found")
