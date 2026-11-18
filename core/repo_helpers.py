"""Pre and postconditions of the Repositories tests, used by the fixtures in tests/repositories/conftest.py.

They replace the pre-request scripts and the "99_Teardown" folder of the Postman collection.
Unlike issues, repositories can be deleted, but a delete is irreversible, so every delete in this
module goes through the same safety checks: only repositories that start with settings.TEST_REPO_PREFIX,
and never the fixed repository of the read-only tests (settings.READ_REPO).
"""
import time

from config import settings
from config.settings import Endpoints


def is_test_repo(name):
    """True only for repositories created by these tests."""
    return name.startswith(settings.TEST_REPO_PREFIX) and name != settings.READ_REPO


def create_repo(client, name, **extra):
    response = client.post(Endpoints.USER_REPOS, json={"name": name, **extra})
    assert response.status_code == 201, f"Precondition failed: could not create '{name}' ({response.status_code})"
    return response.json()


def delete_repo(client, name):
    """Returns the response. Refuses to delete anything that is not a test repository."""
    assert is_test_repo(name), f"Refusing to delete '{name}': it is not a test repository"
    return client.delete(Endpoints.repository(name))


def cleanup_repos(client, names):
    """Deletes the test repositories in the list. A 404 is fine: the test may have deleted it or it was never created.
    It does not raise: a failed cleanup must not hide the real result of the test."""
    for name in names:
        if not is_test_repo(name):
            print(f"[Cleanup] Skipped '{name}': it is not a test repository")
            continue
        response = client.delete(Endpoints.repository(name))
        if response.status_code not in (204, 404):
            print(f"[Cleanup] Could not delete '{name}': {response.status_code}")
    names.clear()


def delete_leftovers(client):
    """Deletes the test repositories of OWNER left by an interrupted run (session cleanup).
    It only looks at repositories owned by OWNER and whose name starts with the test prefix."""
    response = client.get(Endpoints.USER_REPOS, params={"affiliation": "owner", "sort": "created", "direction": "desc", "per_page": 100})
    if response.status_code != 200:
        print(f"[Cleanup] Could not list repositories to look for leftovers: {response.status_code}")
        return
    for repo in response.json():
        if repo["owner"]["login"].lower() == settings.OWNER.lower() and is_test_repo(repo["name"]):
            result = client.delete(Endpoints.repository(repo["name"]))
            print(f"[Cleanup] Leftover '{repo['name']}' deleted: {result.status_code}")


def pause():
    """GitHub limits the creation of content (secondary rate limit): wait after tests that create repositories."""
    time.sleep(settings.REPO_PAUSE_SECONDS)
