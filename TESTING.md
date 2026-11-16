# GitHub Issues API - pytest framework (SQE3, Lab A.3)

API tests for the **Issues** feature of the GitHub REST API, migrated from the Lab 2 Postman collection (30 test cases).

| Piece | Tool |
|---|---|
| HTTP client | requests |
| Test runner + hooks (fixtures) | pytest |
| Assertions | plain `assert` (pytest assertion rewriting) |
| Parameter types | jsonschema |
| Test data | Faker |
| Config / secrets | python-dotenv (`.env`) |
| Reports | pytest-html, JUnit XML |

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (source .venv/bin/activate on Linux/macOS)
pip install -r requirements.txt
copy .env.example .env          # then paste the token in GITHUB_TOKEN
```

The token is a fine-grained PAT with **Issues: read and write** only on the test repository. `.env` is in `.gitignore`.
Without a token, only the tests marked `no_token` and the POCs run; the rest are skipped.

## Run

```bash
pytest                                   # everything
pytest tests/poc                         # proofs of concept (no token needed)
pytest -m smoke                          # one happy path per endpoint
pytest -m "negative or boundary"         # by type of test
pytest --html=reports/report.html --self-contained-html --junitxml=reports/junit.xml
```

## Structure

```
config/settings.py      variables from .env, endpoints and constants
core/api_client.py      requests.Session with base URL, headers and token
core/assertions.py      common checks, schema validation, error checks
core/schemas.py         issue and error JSON schemas
core/data_factory.py    random data with Faker
core/issue_helpers.py   pre/postconditions (create, close, lock, cleanup, wait_until)
tests/conftest.py       fixtures (hooks) shared by all tests
tests/poc/              proofs of concept of requests and pytest
tests/issues/           one file per endpoint: auth, post, patch, get, lock, e2e
```

## Conventions

- Files `test_<endpoint>.py`; functions `test_<tc_id>_verify_that_...`, so the Lab 1 ID shows in the report.
- Markers: `smoke`, `negative`, `boundary`, `e2e`, `no_token` (declared in `pytest.ini`, `--strict-markers` on).
- Every test checks status code, headers, body and, where it applies, schema and data integrity (a second GET).
- Each test creates its own data through fixtures and cleans it up after `yield`. GitHub does not allow deleting issues, so cleanup closes them as `not_planned`.

---

# Labels and Milestones 

API tests for the **Labels** and **Milestones** features, migrated from the Lab 2 Postman collection: 49 test cases (20 for Labels and 29 for Milestones). They use the same framework as the Issues tests.

## Setup for these tests

Each member tests in their own repository, so `.env` must point to it:

```
OWNER=<your GitHub user>
REPO=<your test repository>
GITHUB_TOKEN=<token with write access to Issues on that repository>
```

Labels and milestones are managed with the **Issues** permission of a fine-grained token. The repository must be public: the authentication tests read the result without a token.

## Run

```bash
pytest tests/labels tests/milestones                   # the 49 test cases
pytest tests/labels                                    # only Labels
pytest tests/milestones -m "negative or boundary"      # by type of test
pytest tests/poc/test_poc_labels_milestones.py         # proofs of concept
```

## Structure

```
core/label_helpers.py        create / rename / delete / cleanup of labels
core/milestone_helpers.py    create / delete / cleanup of milestones
core/label_assertions.py     checks shared by the Labels tests
tests/labels/conftest.py     fixtures: label_names_to_clean_up, existing_label, deleted_label, renamed_label
tests/milestones/conftest.py fixtures: milestone_numbers_to_clean_up, existing_milestone, deleted_milestone
tests/labels/                test_labels_post, get, patch, delete, auth
tests/milestones/            test_milestones_post, get, patch, delete, auth
```

## Notes

- Every test creates its own data with the prefix `qa-pm-` and deletes it after `yield` (labels and milestones can be deleted through the API, unlike issues). A session fixture also removes any `qa-pm-` leftovers before and after the run.
- The read-only milestone tests share three milestones created once by the `read_only_milestones` module fixture in `test_milestones_get.py`.
- `TC_LABEL_POST_002` fails on purpose: the endpoint accepts a label without color (201) instead of the 422 expected in Lab 1. The expected result was not changed.
- Test cases `*_AUTH_*` and `*_PERM_*` were added after the feedback of Group 2; they are not in the Lab 1 table.
