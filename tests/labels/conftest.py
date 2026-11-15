"""Fixtures of the Labels tests. The shared ones (github, anonymous, invalid_client) are in tests/conftest.py."""
from dataclasses import dataclass

import pytest

from core import data_factory
from core.label_helpers import cleanup_labels, create_label, delete_label, remove_leftover_labels, rename_label


@dataclass
class RenamedLabel:
    old_name: str
    new_name: str


def _test_case_id(request):
    test_name_before_description = request.node.name.split("_verify")[0]
    return test_name_before_description.removeprefix("test_")


@pytest.fixture(scope="session", autouse=True)
def remove_leftover_test_labels_before_and_after_session(github):
    remove_leftover_labels(github)
    yield
    remove_leftover_labels(github)


@pytest.fixture
def label_names_to_clean_up(github):
    names = []
    yield names
    cleanup_labels(github, names)


@pytest.fixture
def existing_label(github, label_names_to_clean_up, request):
    label = create_label(github, _test_case_id(request))
    label_names_to_clean_up.append(label["name"])
    return label


@pytest.fixture
def deleted_label(github, existing_label):
    response = delete_label(github, existing_label["name"])
    assert response.status_code == 204, f"Precondition failed: could not delete '{existing_label['name']}' ({response.status_code})"
    return existing_label


@pytest.fixture
def renamed_label(github, existing_label, label_names_to_clean_up, request):
    new_name = data_factory.label_name(_test_case_id(request))
    label_names_to_clean_up.append(new_name)
    rename_label(github, existing_label["name"], new_name)
    return RenamedLabel(old_name=existing_label["name"], new_name=new_name)