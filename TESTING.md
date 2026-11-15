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
