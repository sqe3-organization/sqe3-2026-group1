"""POST /user/repos (folder 01_POST_Create_Repo of the Postman collection): the cases that need no repository first.

POST_004 and POST_009 use the repo_names_to_clean_up fixture (reviewer suggestion of Group 2): in Postman the
names were local variables, so no cleanup could find the repository if the API created it by mistake."""
import pytest

from config.settings import Endpoints
from core import data_factory
from core.assertions import assert_common, assert_error, assert_schema
from core.schemas import ERROR_SCHEMA


@pytest.mark.negative
def test_tc_repo_post_004_verify_that_the_api_does_not_create_a_repo_without_a_token(anonymous, github, repo_names_to_clean_up):
    name = data_factory.repo_name("TC_REPO_POST_004")
    repo_names_to_clean_up.append(name)  # in case the API creates it by mistake
    response = anonymous.post(Endpoints.USER_REPOS, json={"name": name})

    assert_error(response, 401, "Requires authentication")
    # data integrity: the repository was not created
    assert github.get(Endpoints.repository(name)).status_code == 404


@pytest.mark.negative
@pytest.mark.no_token
def test_tc_repo_post_005_verify_that_the_api_rejects_a_request_with_an_invalid_token(invalid_client):
    response = invalid_client.post(Endpoints.USER_REPOS, json={"name": data_factory.repo_name("TC_REPO_POST_005")})

    assert_error(response, 401, "Bad credentials")


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


@pytest.mark.negative
def test_tc_repo_post_009_verify_that_creating_a_repo_with_a_token_without_permission_returns_403(no_admin_client, repo_names_to_clean_up):
    name = data_factory.repo_name("TC_REPO_POST_009")
    repo_names_to_clean_up.append(name)  # in case the API creates it by mistake
    response = no_admin_client.post(Endpoints.USER_REPOS, json={"name": name})

    assert response.status_code == 403
    assert_common(response)
    assert isinstance(response.json()["message"], str) and response.json()["message"] != ""
    assert_schema(response.json(), ERROR_SCHEMA)
