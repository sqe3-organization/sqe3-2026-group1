"""Fixtures used by the Gists tests.
The shared clients (github, anonymous and invalid_client) are defined
in the main tests/conftest.py file.
"""

import time

import pytest

from core import gist_helpers

PAUSE_BETWEEN_TESTS_SECONDS = 0.5

def _test_case_id(request):
    return request.node.name.split("_verify")[0].removeprefix("test_")

@pytest.fixture(scope="session", autouse=True)
def remove_leftover_test_gists_before_and_after_session(github):
    gist_helpers.remove_leftover_gists(github)
    yield
    gist_helpers.remove_leftover_gists(github)


@pytest.fixture(autouse=True)
def pause_between_tests():
    yield
    time.sleep(PAUSE_BETWEEN_TESTS_SECONDS)

@pytest.fixture
def gist_ids_to_clean_up(github):
    ids = []
    yield ids
    gist_helpers.cleanup_gists(github, ids)

@pytest.fixture
def existing_gist(github, gist_ids_to_clean_up, request):
    gist = gist_helpers.create_gist(github, _test_case_id(request))
    gist_ids_to_clean_up.append(gist["id"])
    return gist

@pytest.fixture
def existing_public_gist(github, gist_ids_to_clean_up, request):
    gist = gist_helpers.create_gist(
        github,
        _test_case_id(request),
        files=gist_helpers.build_files("public.txt"),
        public=True
    )
    gist_ids_to_clean_up.append(gist["id"])
    return gist


@pytest.fixture
def deleted_gist(github, existing_gist):
    response = gist_helpers.delete_gist(github, existing_gist["id"])
    assert response.status_code == 204, (
        f"Precondition failed: could not delete the Gist ({response.status_code})"
    )
    return existing_gist