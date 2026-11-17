
from urllib.parse import quote

from config.settings import Endpoints

FOUND_STATUS_CODE = 200
NOT_FOUND_STATUS_CODE = 404


def assert_label_matches(actual_label, expected_label):
    assert actual_label["name"] == expected_label["name"]
    assert actual_label["description"] == expected_label["description"]
    assert_same_color_ignoring_case(actual_label["color"], expected_label["color"])


def assert_same_color_ignoring_case(actual_color, expected_color):
    assert actual_color.lower() == expected_color.lower()


def assert_label_can_be_retrieved(client, label_name):
    response = client.get(Endpoints.label(label_name))
    assert response.status_code == FOUND_STATUS_CODE, f"label '{label_name}' was not found"
    assert response.json()["name"] == label_name


def assert_label_does_not_exist(client, label_name, labels_path=None):
    response = client.get(label_path(label_name, labels_path))
    assert response.status_code == NOT_FOUND_STATUS_CODE, f"label '{label_name}' still exists"


def label_path(label_name, labels_path=None):
    if labels_path is None:
        return Endpoints.label(label_name)
    return f"{labels_path}/{quote(label_name, safe='')}"
