"""Fixtures of the Repositories tests (tests/repositories/conftest.py).
"""
import pytest

from config import settings
from config.settings import Endpoints
from core.api_client import GitHubClient
from core.repo_helpers import cleanup_repos, delete_leftovers, pause


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


# ----------------------------------------------------------------- cleanup
@pytest.fixture(scope="session", autouse=True)
def leftovers_cleanup(github):
    if settings.TOKEN:
        delete_leftovers(github)
    yield
    if settings.TOKEN:
        delete_leftovers(github)


@pytest.fixture
def repo_names_to_clean_up(github):
    names = []
    yield names
    cleanup_repos(github, names)
    pause()
