"""POC 2 - Test runner (pytest).
Goal: understand fixtures as hooks (setup/teardown and scopes), the xUnit-style hooks,
plain assert, parametrize and markers. No HTTP calls."""
import pytest

ORDER = []


@pytest.fixture(scope="module")
def module_resource():
    ORDER.append("module setup (once per file)")
    yield "shared"
    ORDER.append("module teardown")
    print("\nHook execution order:\n - " + "\n - ".join(ORDER))


@pytest.fixture
def resource(module_resource):
    ORDER.append("function setup (before each test)")
    yield {"id": 1}
    ORDER.append("function teardown (after each test, even if it fails)")


def test_fixture_gives_data_to_the_test(resource):
    ORDER.append("test 1")
    assert resource["id"] == 1


def test_second_test_gets_a_new_function_fixture(resource):
    ORDER.append("test 2")
    assert ORDER.count("function setup (before each test)") == 2


class TestXUnitStyleHooks:
    """The same idea with the classic setup/teardown methods (like JUnit or unittest)."""

    def setup_method(self):
        self.items = ["bug"]

    def teardown_method(self):
        self.items.clear()

    def test_setup_method_ran(self):
        assert self.items == ["bug"]


@pytest.mark.parametrize("per_page, expected", [(1, 1), (100, 100), (101, 100)])
def test_parametrize_runs_one_test_per_row(per_page, expected):
    assert min(per_page, 100) == expected


def test_plain_assert_shows_the_values_on_failure():
    issue = {"number": 7, "labels": [{"name": "bug"}], "closed_at": None}
    assert isinstance(issue["number"], int)
    assert "bug" in [label["name"] for label in issue["labels"]]
    assert issue["closed_at"] is None


def test_expected_exception():
    with pytest.raises(KeyError):
        {}["missing"]
