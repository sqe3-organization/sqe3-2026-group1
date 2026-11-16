"""DELETE /repos/{owner}/{repo}/labels/{name} (Delete a label)."""
import pytest

from config.settings import Endpoints
from core.assertions import assert_no_content
from core.label_assertions import assert_label_does_not_exist


@pytest.mark.smoke
def test_tc_label_delete_001_verify_that_an_existing_label_can_be_deleted(github, existing_label):
    response = github.delete(Endpoints.label(existing_label["name"]))
    assert_no_content(response)


@pytest.mark.negative
def test_tc_label_delete_002_verify_that_a_deleted_label_can_no_longer_be_retrieved(github, deleted_label):
    assert_label_does_not_exist(github, deleted_label["name"])