"""Helper functions to prepare and clean up Gists during the tests.

These functions replace the Setup and 99 - Teardown folders from Postman.
"""

from config import settings
from config.settings import Endpoints
from core import data_factory

TEST_PREFIX = "qa-pm-"
MAIN_FILE = "hello.py"
SECOND_FILE = "keep.txt"


def build_files(*names):
    return {name: {"content": data_factory.file_content()} for name in names}


def create_gist(client, tc_id, files=None, public=False, **extra):
    """Creates a test Gist with two files by default.

    Having two files allows a test to delete one without leaving the Gist empty.
    """
    payload = {
        "description": data_factory.gist_description(tc_id),
        "public": public,
        "files": files if files is not None else build_files(MAIN_FILE, SECOND_FILE),
        **extra,
    }

    response = client.post(Endpoints.GISTS, json=payload)

    assert response.status_code == 201, (
        f"Could not create the test Gist: {response.status_code}"
    )

    return response.json()


def get_gist(client, gist_id):
    return client.get(Endpoints.gist(gist_id))


def delete_gist(client, gist_id):
    return client.delete(Endpoints.gist(gist_id))


def cleanup_gists(client, gist_ids):
    """Deletes the Gists created during a test.
    A 404 response is accepted because a test may have already deleted the Gist.
    """
    for gist_id in gist_ids:
        response = delete_gist(client, gist_id)

        if response.status_code not in (204, 404):
            print(
                f"[Cleanup] Could not delete Gist '{gist_id}': "
                f"{response.status_code}"
            )

    gist_ids.clear()


def remove_leftover_gists(client):
    """Removes test Gists left behind by a previous test run."""
    if not settings.TOKEN:
        return

    response = client.get(Endpoints.GISTS, params={"per_page": 100})

    if response.status_code != 200:
        return

    for gist in response.json():
        description = gist.get("description") or ""

        if description.startswith(TEST_PREFIX):
            delete_gist(client, gist["id"])