"""POST /user/repos (folder 01_POST_Create_Repo of the Postman collection).

POST_004 and POST_009 use the repo_names_to_clean_up fixture (reviewer suggestion of Group 2): in Postman the
names were local variables, so no cleanup could find the repository if the API created it by mistake.

POST_001, POST_002, POST_003 and POST_008 create their own repositories and register them in
repo_names_to_clean_up for teardown.

POST_007 uses shared_public_repo (session scope) to attempt a duplicate-name creation without
an extra repository creation of its own.
"""
import pytest

from config import settings
from config.settings import Endpoints
from core import data_factory
from core.assertions import assert_common, assert_error, assert_schema
from core.schemas import ERROR_SCHEMA, REPO_SCHEMA


# ----------------------------------------------------------------- POST_001: create with name only
@pytest.mark.smoke
def test_tc_repo_post_001_verify_that_creating_a_repo_with_only_name_returns_201(github, repo_names_to_clean_up):
    name = data_factory.repo_name("TC_REPO_POST_001")
    repo_names_to_clean_up.append(name)
    response = github.post(Endpoints.USER_REPOS, json={"name": name})

    assert response.status_code == 201
    assert_common(response)
    repo = response.json()
    assert isinstance(repo["id"], int)
    assert repo["name"] == name
    assert repo["full_name"] == f"{settings.OWNER}/{name}"
    assert isinstance(repo["html_url"], str) and repo["html_url"]
    assert isinstance(repo["created_at"], str) and repo["created_at"]
    assert_schema(repo, REPO_SCHEMA)


# ----------------------------------------------------------------- POST_002: create with name, description and private:false
@pytest.mark.smoke
def test_tc_repo_post_002_verify_that_creating_a_repo_with_name_description_and_private_false_returns_201(github, repo_names_to_clean_up):
    name = data_factory.repo_name("TC_REPO_POST_002")
    repo_names_to_clean_up.append(name)
    payload = {"name": name, "description": "API test repo - public", "private": False}
    response = github.post(Endpoints.USER_REPOS, json=payload)

    assert response.status_code == 201
    assert_common(response)
    repo = response.json()
    assert repo["description"] == "API test repo - public"
    assert repo["visibility"] == "public"
    assert "Location" in response.headers
    assert_schema(repo, REPO_SCHEMA)


# ----------------------------------------------------------------- POST_003: created repo is immediately reachable by GET
def test_tc_repo_post_003_verify_that_the_created_repo_is_immediately_reachable_by_get(github, repo_names_to_clean_up):
    name = data_factory.repo_name("TC_REPO_POST_003")
    repo_names_to_clean_up.append(name)
    response = github.post(
        Endpoints.USER_REPOS,
        json={"name": name, "description": "API test repo - POST_003", "private": False},
    )

    assert response.status_code == 201
    assert_common(response)
    # Integrity: the created repository must be reachable immediately via GET
    get_response = github.get(Endpoints.repository(name))
    assert get_response.status_code == 200
    assert_common(get_response)
    assert get_response.json()["name"] == name
    assert get_response.json()["description"] == "API test repo - POST_003"


# ----------------------------------------------------------------- POST_004: 401 without token
@pytest.mark.negative
def test_tc_repo_post_004_verify_that_the_api_does_not_create_a_repo_without_a_token(anonymous, github, repo_names_to_clean_up):
    name = data_factory.repo_name("TC_REPO_POST_004")
    repo_names_to_clean_up.append(name)  # in case the API creates it by mistake
    response = anonymous.post(Endpoints.USER_REPOS, json={"name": name})

    assert_error(response, 401, "Requires authentication")
    # data integrity: the repository was not created
    assert github.get(Endpoints.repository(name)).status_code == 404


# ----------------------------------------------------------------- POST_005: 401 with invalid token
@pytest.mark.negative
@pytest.mark.no_token
def test_tc_repo_post_005_verify_that_the_api_rejects_a_request_with_an_invalid_token(invalid_client):
    response = invalid_client.post(Endpoints.USER_REPOS, json={"name": data_factory.repo_name("TC_REPO_POST_005")})

    assert_error(response, 401, "Bad credentials")


# ----------------------------------------------------------------- POST_006: 422 without name (known discrepancy)
@pytest.mark.negative
def test_tc_repo_post_006_verify_that_creating_a_repo_without_name_returns_422(github):
    response = github.post(Endpoints.USER_REPOS, json={"description": "No name"})

    assert response.status_code == 422
    assert_common(response)
    body = response.json()
    # Expected result of Lab 1, not changed. In the Lab 2 runs GitHub answered 422 with the message
    # "New repository name must not be blank", so this assertion fails (observation, not yet compared with the docs).
    assert body["message"] == "Validation Failed"
    assert isinstance(body["errors"], list) and len(body["errors"]) > 0
    assert_schema(body, ERROR_SCHEMA)


# ----------------------------------------------------------------- POST_007: 422 for duplicate name
@pytest.mark.negative
def test_tc_repo_post_007_verify_that_creating_a_repo_with_a_duplicate_name_returns_422(github, shared_public_repo):
    # shared_public_repo is a session-scoped public repository that already exists under OWNER.
    # Attempting to create a repository with the same name must return 422.
    # Finding (Newman run): GitHub returned 'Repository creation failed.' instead of 'Validation Failed'.
    # The original Postman assertion is preserved to document the discrepancy.
    # Do not change this assertion to make the test pass.
    response = github.post(Endpoints.USER_REPOS, json={"name": shared_public_repo})

    assert response.status_code == 422
    assert_common(response)
    body = response.json()
    assert body["message"] == "Validation Failed"
    assert isinstance(body.get("errors"), list) and len(body["errors"]) > 0
    name_error = next((e for e in body["errors"] if e.get("field") == "name"), None)
    assert name_error is not None
    assert_schema(body, ERROR_SCHEMA)


# ----------------------------------------------------------------- POST_008: private defaults to false when not specified
def test_tc_repo_post_008_verify_that_a_repo_created_without_the_private_field_is_public_by_default(github, repo_names_to_clean_up):
    name = data_factory.repo_name("TC_REPO_POST_008")
    repo_names_to_clean_up.append(name)
    response = github.post(Endpoints.USER_REPOS, json={"name": name})

    assert response.status_code == 201
    assert_common(response)
    repo = response.json()
    assert repo["private"] is False
    assert repo["visibility"] == "public"
    assert repo["name"] == name
    assert_schema(repo, REPO_SCHEMA)


# ----------------------------------------------------------------- POST_009: 403 without admin permission
@pytest.mark.negative
def test_tc_repo_post_009_verify_that_creating_a_repo_with_a_token_without_permission_returns_403(no_admin_client, repo_names_to_clean_up):
    name = data_factory.repo_name("TC_REPO_POST_009")
    repo_names_to_clean_up.append(name)  # in case the API creates it by mistake
    response = no_admin_client.post(Endpoints.USER_REPOS, json={"name": name})

    assert response.status_code == 403
    assert_common(response)
    assert isinstance(response.json()["message"], str) and response.json()["message"] != ""
    assert_schema(response.json(), ERROR_SCHEMA)
