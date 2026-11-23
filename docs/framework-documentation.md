# Framework Documentation

## Overview

The **SQE3** project provides a Python‑based test framework for the GitHub REST API.  It is organized in **layers** that separate concerns:

```
+-------------------+-------------------------------+
| Layer            | Responsibility                |
+-------------------+-------------------------------+
| Config            | Load environment variables,   |
|                  | expose constants and endpoint |
|                  | definitions.                  |
+-------------------+-------------------------------+
| Infrastructure    | `core.request_manager` – a    |
|                  | singleton that owns a          |
|                  | `requests.Session`, adds        |
|                  | request/response logging.      |
+-------------------+-------------------------------+
| Client            | `core.api_client.GitHubClient`|
|                  | builds URLs from `Endpoints`, |
|                  | injects the token, delegates   |
|                  | all HTTP verbs to the manager. |
+-------------------+-------------------------------+
| Helpers (pre‑/   | `core/*_helpers.py` – create, |
| post‑conditions) | delete, and clean up resources |
|                  | (issues, labels, repos, …).   |
+-------------------+-------------------------------+
| Assertions        | `core.assertions` – reusable   |
|                  | checks (status, schema, time, |
|                  | error bodies).                |
+-------------------+-------------------------------+
| Data Factory      | `core.data_factory` – deterministic |
|                  | fake data (repo names, issue   |
|                  | titles, etc.) using Faker.    |
+-------------------+-------------------------------+
| Logging & Report  | `core.logger` – dual output   |
|                  | (console + rotating file).    |
|                  | `core.run_logging` logs test   |
|                  | phases, `core.log_report` builds |
|                  | a markdown report after the run. |
+-------------------+-------------------------------+
| Tests & Fixtures  | `tests/` – pytest suite.      |
|                  | Global fixtures in `tests/conftest.py`
|                  | provide the client, session,  |
|                  | and cleanup helpers.          |
+-------------------+-------------------------------+
```

### Key Modules

| Module | Main Class / Functions | Purpose |
|---|---|---|
| `core/request_manager.py` | `RequestManager` (singleton) | Holds a shared `requests.Session`, adds default headers, logs every request. |
| `core/api_client.py` | `GitHubClient` | Thin wrapper that adds the **Authorization** header and forwards calls to `RequestManager`. |
| `core/logger.py` | `configure_logging`, `get_logger` | Sets up a console `StreamHandler` and a rotating file `FileHandler`. Redacts tokens from log messages. |
| `core/run_logging.py` | `LOG_LEVEL_BY_OUTCOME`, `summarize_test_result` | Hooked by pytest to emit a one‑line result per test (`PASS`, `FAIL`, `ERROR`, `SKIP`). |
| `core/log_report.py` | `generate_report` (called from pytest hook) | Reads the run log file and produces a Markdown summary (passes, failures, timings). |
| `core/cleanup_logging.py` | `log_cleanup_result` | Unified logging for cleanup helpers (info / warning / error). |
| `core/*_helpers.py` | `create_repo`, `delete_repo`, `cleanup_repos`, `delete_leftovers` | Pre‑condition helpers (create resources) and post‑condition helpers (safe deletion). |
| `core/assertions.py` | `assert_common`, `assert_schema`, `assert_error` | Generic response validation (status, timeliness, JSON schema). |
| `core/data_factory.py` | Functions like `repo_name`, `issue_title` | Generates unique names prefixed with `settings.TEST_REPO_PREFIX` so that cleanup can locate leftovers. |
| `config/settings.py` | `Endpoints`, environment constants | Central place for URL templates and global settings (tokens, rate‑limit thresholds). |
| `tests/` | pytest test files per API module | Follow the **Arrange‑Act‑Assert** pattern, use fixtures from `tests/conftest.py` and module‑specific fixtures. |

### Test Organization

* **Core tests** (`tests/core/`) verify the framework itself – request manager, logger, run‑logging, cleanup helpers.
* **API tests** (`tests/issues/`, `tests/labels/`, `tests/milestones/`, `tests/gists/`, `tests/repositories/`) exercise the real GitHub endpoints.  Fixtures create resources, store their names in a list, and `cleanup_repos`/`cleanup_issues` ensure safe teardown.
* **PoC tests** (`tests/poc/`) compare HTTP client libraries (`requests`, `httpx`, `aiohttp`, `urllib`).
* **Search tests** (`tests/search/`) cover the read‑only Search API (added in Activity 5).  They are mocked where possible; the real API requires a valid **search** scope token.

### Logging Strategy

* Every log line is formatted as:
  ```
  {asctime} | {hostname} | {worker} | {LEVEL:<7} | {message}
  ```
* `configure_logging(level, directory)` creates the log file `logs/test_run_<timestamp>.log`.
* The **framework logger** (`framework`) never logs the raw token – `redact_secrets` masks `Bearer …` and any GitHub PAT.
* Test phases (`setup`, `call`, `teardown`) are logged via pytest hooks in `tests/conftest.py`.
* Cleanup helpers use `log_cleanup_result` which emits:
  * `INFO` – successful deletion (`Cleanup: repo X deleted`).
  * `WARNING` – resource already absent (`Cleanup: repo X was already deleted`).
  * `ERROR` – unexpected status (`Cleanup failed for repo X …`).

### Report Generation

After the test run finishes, `core.log_report.generate_report` reads the log file and produces a Markdown document containing:
* Summary table (tests passed / failed, total duration).
* Per‑test outcome lines with outcome, duration, and optional reason.
* This report is displayed by the pytest terminal summary (`Log file of this run: …`).

### Extensibility

* Adding a new API module only requires:
  1. A **helper** in `core/` that implements the pre/post logic.
  2. Corresponding **assertion** helpers if custom validation is needed.
  3. Fixtures in `tests/<module>/conftest.py` that use the helper.
  4. Test files under `tests/<module>/` that follow the existing naming convention.
* The logging and reporting infrastructure works automatically – new modules just call `get_logger(__name__)`.

---

*This documentation is generated from the actual source code and reflects the current state of the `feature/TICKET-18-extend-test-coverage-and-documentation` branch.*
