
# Test organization

How the tests are organized by application area, by type of test, by priority and by execution stage.
The classification is applied by `core/classification.py` when pytest collects the tests, so
every subset of the suite can be run with `pytest -m`.

## 1. Area and type

| Level | Where it is | Example |
|---|---|---|
| Application area | one folder per area under `tests/` | `tests/labels/` |
| Endpoint and operation | one file per HTTP operation | `test_labels_post.py` |
| Authentication | one file per area | `test_labels_auth.py` |
| Chained flows | one file per area | `test_e2e.py` |
| Type of test | a marker on every test | `negative`, `boundary`, `e2e`, `happy_path` |

A new test goes into the file of its endpoint and operation. A new endpoint gets its own file.
The type is written in the test with `@pytest.mark.negative`, `@pytest.mark.boundary` or
`@pytest.mark.e2e`. A test with none of them is a happy path and receives `happy_path` automatically.
The area is the folder, so it is never written in the test: it is added as a marker with the folder name.

## 2. Priority

The priority follows the test plan of Lab 1: happy paths and authentication are high, validation
errors are medium and limits are low. The first rule that applies wins:

| Rule | Priority |
|---|---|
| The test carries its own `p1`, `p2` or `p3` marker | the one written |
| Smoke tests and authentication tests | `p1` (high) |
| Boundary tests | `p3` (low) |
| Any other test (remaining happy paths, negative, e2e) | `p2` (medium) |

To change the priority of one test, write the marker on the test:

```python
@pytest.mark.p1
@pytest.mark.negative
def test_tc_iss_post_006_verify_that_an_issue_cannot_be_created_in_a_non_existent_repository(github):
    ...
```

## 3. Execution stage

| Stage | Marker | Tests | When to run it |
|---|---|---|---|
| Smoke | `smoke` | the main happy path of each endpoint | after every change and before the other stages |
| Regression | `regression` | every test of an area folder | before merging a release |

Smoke tests are always `p1`, so `-m p1` contains the smoke tests plus the authentication tests.

## 4. Commands

```bash
pytest -m smoke                         # smoke stage
pytest -m regression                    # regression stage
pytest -m p1                            # only high priority
pytest -m "p1 or p2"                    # high and medium priority
pytest -m "labels and p1"               # high priority of one area
pytest -m "negative and not p3"         # one type, without the low priority
pytest -m "regression and not smoke"    # regression without repeating the smoke tests
```

## 5. Current distribution

Counted with `pytest --collect-only -m "<area> and <priority>"` over the 145 tests of the area folders.

| Area | p1 | p2 | p3 | Smoke | Total |
|---|---|---|---|---|---|
| gists | 4 | 19 | 1 | 3 | 24 |
| issues | 6 | 20 | 4 | 5 | 30 |
| labels | 8 | 8 | 4 | 5 | 20 |
| milestones | 8 | 17 | 4 | 5 | 29 |
| repositories | 3 | 26 | 0 | 3 | 29 |
| search | 2 | 11 | 0 | 2 | 13 |
| **Total** | **31** | **101** | **13** | **23** | **145** |

| Type | Tests |
|---|---|
| happy_path | 71 |
| negative | 61 |
| boundary | 13 |
| e2e | 4 |

A test can have two types (a boundary test that is also negative), so the types add up to more than 145.