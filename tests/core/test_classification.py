"""Unit tests of the classification of the tests (core/classification.py).

They do not call GitHub, so they run without a token.
"""
import pytest

from core.classification import (
    AREA_NAMES,
    decide_markers_to_add,
    decide_priority,
    decide_type_markers,
    find_area,
)

pytestmark = pytest.mark.no_token


@pytest.mark.parametrize("area_name", AREA_NAMES)
def test_the_area_is_the_folder_of_the_test(area_name):
    assert find_area(f"/project/tests/{area_name}/test_anything.py") == area_name


@pytest.mark.parametrize("folder_name", ["core", "poc"])
def test_tests_outside_the_area_folders_have_no_area(folder_name):
    assert find_area(f"/project/tests/{folder_name}/test_anything.py") is None


def test_a_test_without_another_type_is_a_happy_path():
    assert decide_type_markers({"smoke"}) == ["happy_path"]


@pytest.mark.parametrize("written_type", ["negative", "boundary", "e2e"])
def test_a_test_with_a_written_type_is_not_marked_as_happy_path(written_type):
    assert decide_type_markers({written_type}) == []


def test_a_smoke_test_has_high_priority():
    assert decide_priority({"smoke"}, "tests/issues/test_get.py") == "p1"


def test_an_authentication_test_has_high_priority():
    assert decide_priority({"negative"}, "tests/labels/test_labels_auth.py") == "p1"


def test_a_boundary_test_has_low_priority():
    assert decide_priority({"boundary"}, "tests/issues/test_get.py") == "p3"


def test_a_boundary_test_that_is_also_negative_has_low_priority():
    assert decide_priority({"negative", "boundary"}, "tests/labels/test_labels_post.py") == "p3"


@pytest.mark.parametrize("written_markers", [{"negative"}, {"e2e"}, set()])
def test_the_other_tests_have_medium_priority(written_markers):
    assert decide_priority(written_markers, "tests/issues/test_post.py") == "p2"


def test_a_priority_written_in_the_test_wins_over_the_rules():
    assert decide_priority({"smoke", "p3"}, "tests/issues/test_get.py") == "p3"


def test_a_classified_test_receives_area_stage_type_and_priority():
    markers = decide_markers_to_add({"smoke"}, "tests/gists/test_gists_get.py")

    assert markers == ["gists", "regression", "happy_path", "p1"]


def test_a_test_with_its_own_priority_does_not_receive_a_second_one():
    markers = decide_markers_to_add({"negative", "p1"}, "tests/gists/test_gists_get.py")

    assert markers == ["gists", "regression"]


def test_tests_outside_the_area_folders_receive_nothing():
    assert not decide_markers_to_add({"smoke"}, "tests/core/test_logger.py")