"""Fixtures of the Repositories tests (tests/repositories/conftest.py).
"""
import pytest

from config import settings
from config.settings import Endpoints
from core.api_client import GitHubClient


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
