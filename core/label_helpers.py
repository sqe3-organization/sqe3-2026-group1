"""Pre and postconditions for the Labels tests, used by the fixtures in tests/labels/conftest.py.

They replace the Setup and Teardown folders of the Postman collection. Unlike issues, labels
can be deleted through the API, so the cleanup really removes them.
"""
from config import settings
from config.settings import Endpoints
from core import data_factory

TEST_PREFIX = "qa-pm-"


def create_label(client, tc_id, **extra):
    payload = {
        "name": data_factory.label_name(tc_id),
        "color": "1D76DB",
        "description": "Temporary label for API testing",
        **extra,
    }
    response = client.post(Endpoints.LABELS, json=payload)
    assert response.status_code == 201, f"Precondition failed: could not create the label ({response.status_code})"
    return response.json()


def rename_label(client, name, new_name):
    response = client.patch(Endpoints.label(name), json={"new_name": new_name})
    assert response.status_code == 200, f"Precondition failed: could not rename '{name}' ({response.status_code})"
    return response.json()


def delete_label(client, name):
    return client.delete(Endpoints.label(name))


def cleanup_labels(client, names):
    """Deletes the labels the test created. 404 is fine: the test may have deleted or renamed it.
    It does not raise: a failed cleanup must not hide the real result of the test."""
    for name in names:
        response = delete_label(client, name)
        if response.status_code not in (204, 404):
            print(f"[Cleanup] Could not delete label '{name}': {response.status_code}")
    names.clear()


def remove_leftover_labels(client):
    """Session cleanup: deletes any qa-pm-* label left by an interrupted run.
    Default labels and labels without the prefix are never touched."""
    if not settings.TOKEN:
        return
    response = client.get(Endpoints.LABELS, params={"per_page": 100})
    if response.status_code != 200:
        return
    for label in response.json():
        if label["name"].startswith(TEST_PREFIX):
            delete_label(client, label["name"])