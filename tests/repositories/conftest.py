"""Fixtures of the Repositories tests (tests/repositories/conftest.py).
"""
import pytest

from config import settings
from config.settings import Endpoints
from core import data_factory
from core.api_client import GitHubClient
from core.repo_helpers import cleanup_repos, create_repo, delete_leftovers, pause


# ----------------------------------------------------------------- clients (session scope)
@pytest.fixture(scope="session")
def repo_only_client():
    """Classic token with the repo scope only (tokenRepoOnly in Postman): it cannot delete repositories."""
    if not settings.TOKEN_REPO_ONLY:
        pytest.skip("TOKEN_REPO_ONLY is empty in .env")
    return GitHubClient(token=settings.TOKEN_REPO_ONLY)


@pytest.fixture(scope="session")
def no_admin_client():
    """Fine-grained token without Administration (tokenNoAdmin in Postman): it cannot create or change repositories."""
    if not settings.TOKEN_NO_ADMIN:
        pytest.skip("TOKEN_NO_ADMIN is empty in .env")
    return GitHubClient(token=settings.TOKEN_NO_ADMIN)


@pytest.fixture(scope="session")
def read_repo_path():
    """Path of the private repository used by the read-only tests (readRepo in Postman)."""
    if not settings.READ_REPO:
        pytest.skip("READ_REPO is empty in .env")
    return Endpoints.READ_REPOSITORY


# ----------------------------------------------------------------- session-level cleanup (autouse)
@pytest.fixture(scope="session", autouse=True)
def leftovers_cleanup(github):
    """Deletes qa-pm-* test repositories before the session starts (leftovers from previous runs)
    and again after the session ends (safety net for fixtures that did not clean up).

    Runs delete_leftovers at setup AND teardown.
    Teardown order: leftovers_cleanup is configured before shared_public_repo (autouse fires
    first), so it tears down AFTER shared_public_repo. By the time delete_leftovers runs at
    session end, shared_public_repo has already been deleted and will not appear in the listing.
    """
    if settings.TOKEN:
        delete_leftovers(github)
    yield
    if settings.TOKEN:
        delete_leftovers(github)


# ----------------------------------------------------------------- per-test accumulator (function scope)
@pytest.fixture
def repo_names_to_clean_up(github):
    """[Cleanup] The test appends names it creates; they are deleted in teardown.
    A 404 is accepted: the test may have already deleted the repository.
    pause() is called after cleanup to respect the GitHub secondary rate limit."""
    names = []
    yield names
    cleanup_repos(github, names)
    pause()


# ----------------------------------------------------------------- shared public repository (session scope)
@pytest.fixture(scope="session")
def shared_public_repo(github):
    """Public repository shared by GET_002 and POST_007 for the whole test session.

    scope='session': created once; both tests reuse the same repository without an extra creation.

    Teardown order guarantee: leftovers_cleanup is autouse and is configured before this fixture,
    so its teardown runs AFTER this fixture's teardown. This fixture deletes the repository first;
    when delete_leftovers runs at session end it will not find it and will not attempt a double delete.

    If this fixture's teardown is interrupted (e.g. SIGKILL), the repository has a qa-pm- prefix
    and delete_leftovers at the start of the next session will remove it automatically.
    """
    name = data_factory.repo_name("TC_REPO_SHARED_PUB")
    create_repo(github, name, description="API test repo - public", private=False)
    yield name
    cleanup_repos(github, [name])
    pause()


# ----------------------------------------------------------------- per-test PATCH repository (function scope)
@pytest.fixture
def patch_repo(github):
    """A fresh public repository for each PATCH test.

    Yields a dict:
      'name': str        — original repository name created by this fixture.
      'extra_names': list — mutable list the test can populate with additional names
                           generated during the test (e.g. the renamed name in PATCH_004).

    Teardown deletes the original name and every extra name; accepts 404 for each
    (the original name returns 404 after a rename, which is handled safely).
    """
    name = data_factory.repo_name("TC_REPO_PATCH")
    create_repo(github, name, private=False)
    extra_names = []
    yield {"name": name, "extra_names": extra_names}
    cleanup_repos(github, [name] + extra_names)
    pause()


# ----------------------------------------------------------------- per-test DELETE repository (function scope)
@pytest.fixture
def delete_target_repo(github):
    """A fresh public repository for each DELETE test.

    The test may delete the repository itself; cleanup_repos accepts 404 if already gone.
    """
    name = data_factory.repo_name("TC_REPO_DELETE")
    create_repo(github, name, private=False)
    yield name
    cleanup_repos(github, [name])
    pause()
