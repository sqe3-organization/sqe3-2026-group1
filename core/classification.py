"""Classification of the tests by application area, type of test, priority and execution stage.

Every test collected from an area folder (tests/<area>/) receives these markers automatically,
so any subset can be run with `pytest -m`:

    area        the folder: gists, issues, labels, milestones, repositories, search
    type        happy_path, negative, boundary or e2e (the ones written in the test are kept)
    priority    p1 (high), p2 (medium) or p3 (low), following the priorities of the test plan
    stage       smoke (written in the test) and regression (every classified test)

The priority rules are in `decide_priority` and are documented in docs/test-organization.md.
A test can override the rule by carrying its own p1, p2 or p3 marker.
"""
from pathlib import Path

AREA_NAMES = ("gists", "issues", "labels", "milestones", "repositories", "search")

HAPPY_PATH_MARKER = "happy_path"
NON_HAPPY_PATH_TYPE_MARKERS = ("negative", "boundary", "e2e")
SMOKE_MARKER = "smoke"
REGRESSION_MARKER = "regression"

HIGH_PRIORITY_MARKER = "p1"
MEDIUM_PRIORITY_MARKER = "p2"
LOW_PRIORITY_MARKER = "p3"
PRIORITY_MARKERS = (HIGH_PRIORITY_MARKER, MEDIUM_PRIORITY_MARKER, LOW_PRIORITY_MARKER)

AUTHENTICATION_FILE_NAME_FRAGMENT = "auth"


def find_area(test_file_path):
    """Name of the area folder that contains the test, or None for core, poc and other folders."""
    folder_names = Path(test_file_path).parts
    for area_name in AREA_NAMES:
        if area_name in folder_names:
            return area_name
    return None


def is_authentication_test(test_file_path):
    return AUTHENTICATION_FILE_NAME_FRAGMENT in Path(test_file_path).stem


def decide_type_markers(written_marker_names):
    """Markers of type to add: only happy_path, when the test is none of the other types."""
    is_other_type = any(name in NON_HAPPY_PATH_TYPE_MARKERS for name in written_marker_names)
    return [] if is_other_type else [HAPPY_PATH_MARKER]


def decide_priority(written_marker_names, test_file_path):
    """Priority marker of a test. The first rule that applies wins:

    1. the priority written in the test itself
    2. smoke tests and authentication tests: p1, the service is unusable if they fail
    3. boundary tests: p3, they check limits that are rarely hit
    4. everything else (the other happy paths, negative and e2e tests): p2
    """
    written_priorities = [name for name in PRIORITY_MARKERS if name in written_marker_names]
    if written_priorities:
        return written_priorities[0]
    if SMOKE_MARKER in written_marker_names or is_authentication_test(test_file_path):
        return HIGH_PRIORITY_MARKER
    if "boundary" in written_marker_names:
        return LOW_PRIORITY_MARKER
    return MEDIUM_PRIORITY_MARKER


def decide_markers_to_add(written_marker_names, test_file_path):
    """All the markers that the automatic classification adds to one test.
    It is empty for tests outside the area folders (unit tests of the framework, POCs)."""
    area_name = find_area(test_file_path)
    if area_name is None:
        return []
    markers_to_add = [area_name, REGRESSION_MARKER]
    markers_to_add += decide_type_markers(written_marker_names)
    if not any(name in PRIORITY_MARKERS for name in written_marker_names):
        markers_to_add.append(decide_priority(written_marker_names, test_file_path))
    return markers_to_add