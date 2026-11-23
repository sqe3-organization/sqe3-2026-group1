
# Logger and log report

Every test run writes a log, and a report can be generated from that log.
This document explains the tool, the format, the conventions the whole team follows and the report.

## Tool

The logger is built on Python's standard `logging` module (`core/logger.py`), so it adds no dependency.
We chose it because it already has levels, outputs (handlers) and formats, which is what the activity asks for.

| Piece | Where |
|---|---|
| Logger (levels, console and file outputs, format, token redaction) | `core/logger.py` |
| Result line of each test (`RESULT PASSED \| 312 ms \| ...`) | `core/run_logging.py` |
| Logs of the whole run (start, fixtures, result of each test) | `tests/conftest.py` (pytest hooks) |
| One line per HTTP request | `core/request_manager.py` |
| Cleanup lines shared by all modules | `core/cleanup_logging.py` |
| Report built from the log | `core/log_report.py` |

## Configuration

Two variables in `.env` (documented in `.env.example`, read in `config/settings.py`):

| Variable | Default | Meaning |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Minimum level written. One of `DEBUG`, `INFO`, `WARNING`, `ERROR`. An unknown value stops the run with a clear message |
| `LOG_DIRECTORY` | `logs` | Folder of the log files. It is ignored by git |

The level filters the console and the file, so no code has to be commented out to see less or more.

## Outputs

| Output | What it receives |
|---|---|
| Console | Messages of the framework (requests, helpers, cleanup). pytest only shows what a test printed when that test fails, unless the run uses `-s` |
| Log file `logs/test_run_<date>_<time>.log` | Everything, including the life cycle of the run: `Test run started`, `START <test>`, fixture setup and cleanup, `RESULT <outcome> \| <ms> \| <test>` and `Test run finished` |

pytest already prints START and RESULT in the console (`PASSED`, `FAILED`, ...), so those lines go only to the file to avoid repeating them.
There is one file per run. The run id is shared through the `TEST_RUN_ID` environment variable, so all the workers of a parallel run (pytest-xdist) append to the same file.

## Line format

```
2026-11-22 22:00:08,901 | PC-LUCAS | main | INFO    | Label created with name qa-pm-label-post-001-abc123
date and time           | host     | worker | level  | message
```

| Field | Why it is there |
|---|---|
| Date and time | Order the events and measure time between them |
| Host name | Tell apart a local machine from a pipeline agent |
| Worker | `main`, or the pytest-xdist worker (`gw0`, `gw1`, ...). It lets us follow one worker inside a file shared by parallel runs |
| Level | Filter and search (`grep ERROR`) |
| Message | What happened, following the rules below |

## Levels by layer

| Level | Layer | Use it for | Example |
|---|---|---|---|
| `DEBUG` | Request manager (`RequestManager.send()`) and technical details | The full detail of each request and response. Fixture setup and cleanup. Waits | `POST /repos/o/r/labels -> 201 in 540 ms \| auth=token \| params=None \| request_body={...} \| response_body={...}` |
| `INFO` | Helpers (layer 2) and the life cycle of the run | A short business fact: something was created, renamed, closed, cleaned up. The start, the end and the passed result of a test | `Label created with name qa-pm-label-post-001-abc123` |
| `WARNING` | Any layer | Something unexpected that the framework tolerates. A skipped test | `Cleanup: label qa-pm-x was already deleted` |
| `ERROR` | Any layer | A failure: a failed or error test, a request that raised, a cleanup that did not work | `Cleanup failed for label qa-pm-x \| expected status 204, got 500` |

How to choose when in doubt: if you only need it to find out why a test failed, it is `DEBUG`. If it tells what the test did, it is `INFO`. If someone should look at it even when the tests pass, it is `WARNING`. If something is broken, it is `ERROR`.

Results of a test: `PASSED` is written as `INFO`, `SKIPPED` as `WARNING`, `FAILED` and `ERROR` as `ERROR`.

## How to word a message

1. **Say the fact, in the past tense, starting with the resource.** `Label created with name X`, not `creating label` or `Created!`.
2. **Include the data needed to find the resource** (name, number, id) and nothing else.
3. **Use `%s` arguments, not f-strings:** `logger.info("Label created with name %s", name)`. The text is only built when the level is active.
4. **Use ` | ` to add extra fields** after the sentence: `Could not list the labels to look for leftovers | status=403`.
5. **Write English, one line, no emojis and no decoration.**
6. **Do not repeat what another layer already logs.** A helper does not log the request (the request manager does) and does not log a failed precondition (the assertion message already appears in the `RESULT` line).
7. **Do not use `print` in the framework.** Everything goes through the logger.

## What must be logged

- Every HTTP request and its response status and duration (`DEBUG`, in the request manager).
- Every resource a helper creates or changes (`INFO`).
- The result of every cleanup (`INFO`, `WARNING` or `ERROR`, always through `log_cleanup_result`).
- Leftovers from a previous run that are deleted (`WARNING`).
- The start, the result and the duration of every test.

## What must not be logged

- **Tokens and the `Authorization` header.** The request line only says `auth=token` or `auth=anonymous`. As a safety net, the logger also replaces any bearer token or GitHub token (`ghp_...`, `github_pat_...`) with `[REDACTED]`, even if someone writes one by mistake.
- Passwords or any other secret from `.env`.
- Complete large bodies: the request and response bodies are cut at 500 characters.
- Messages inside loops that would repeat thousands of lines without new information.

## How to add logs to new code

```python
from core.logger import get_logger

logger = get_logger(__name__)

def create_something(client, ...):
    response = client.post(...)
    assert response.status_code == 201, "Precondition failed: ..."   # the assertion explains the failure
    logger.info("Something created with name %s", created["name"])    # the helper tells what it did
```

For a cleanup, call `log_cleanup_result` so the levels are the same in every module.
Use `get_file_only_logger(__name__)` only for lines that pytest already shows in the console.

## Log report

One command, from the root of the repository:

```bash
python -m core.log_report                                 # newest log of LOG_DIRECTORY
python -m core.log_report logs/test_run_20261122_220008.log   # a specific log
```

It prints the report and saves it as Markdown in `reports/` (ignored by git).

| Section | Content |
|---|---|
| Run | Log file, start, duration, exit status of pytest, hosts and workers |
| Totals | Tests per outcome (`PASSED`, `FAILED`, `ERROR`, `SKIPPED`) and pass rate |
| Results per module | The same counts and the time of each module (issues, gists, repositories, labels, milestones) |
| Slowest requests | The 5 slowest requests with status and time |
| Failures | Each `FAILED` or `ERROR` test with the reason |
| Errors and warnings of the framework | Number of warnings and errors, and the first 10 errors |

The slowest requests come from the `DEBUG` lines of the request manager. To have them, run the tests with `LOG_LEVEL=DEBUG`; with a higher level the section says so.
The report reads the log file only: it does not need a token and it does not call GitHub.

## Parallel runs

The format already identifies the worker, so the lines of several workers can live in one file and still be told apart (`grep "| gw2 |"`).
Splitting the log into one file per worker is not implemented. It can be added later if a run needs it.
