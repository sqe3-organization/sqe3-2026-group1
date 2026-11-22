# Request manager (Singleton)

`core/request_manager.py` is the only place of the framework that talks to `requests`.
It follows the **Singleton** pattern: there is one `RequestManager` per test run, and every
module (Issues, Gists, Repositories, Labels and Milestones) sends its requests through it.

## Why a Singleton here

- **One connection pool.** Before, each `GitHubClient` opened its own `requests.Session`
  (3 in `tests/conftest.py` and 2 more in `tests/repositories/conftest.py`). Now the whole run
  shares one session, so TCP/TLS connections to `api.github.com` are reused.
- **One place for the shared configuration.** Base URL, `Accept`, `X-GitHub-Api-Version` and the
  timeout (`REQUEST_TIMEOUT` in `.env`) are set once, from `config/settings.py`.
- **One place to hook cross-cutting features** (for example the logger of Activity 3):
  every request of every module goes through `RequestManager.send()`.

## Design decisions

| Decision | Reason |
|---|---|
| The instance is created in `__new__`, with a class attribute `_instance` | `RequestManager()` and `RequestManager.get_instance()` always return the same object |
| The session is built in `_setup()`, not in `__init__` | Python calls `__init__` on every `RequestManager()`; `_setup()` runs only once |
| Double-checked locking with `threading.Lock` | Two threads cannot create two instances (safe if we add parallel runs later) |
| The token is **not** stored in the Singleton | The auth tests need several identities in the same run (valid, invalid, anonymous, repo-only, no-admin). The token travels with each request |
| `GitHubClient` keeps its public methods (`get`, `post`, `patch`, `put`, `delete`) | No test or helper had to change: a client is now an identity that delegates to the Singleton |
| `RequestManager.reset()` | Closes the session after the last test (`request_manager` fixture) and lets the unit tests start from a clean instance |

## Class diagram

```mermaid
classDiagram
    direction LR
    class RequestManager {
        <<Singleton>>
        -_instance$ : RequestManager
        -_lock$ : threading.Lock
        +base_url : str
        +timeout : float
        +session : requests.Session
        +__new__(cls)$ RequestManager
        +get_instance()$ RequestManager
        +reset()$ None
        -_setup() None
        +send(method, path, token, headers, **kwargs) Response
    }
    class GitHubClient {
        +token : str | None
        +manager : RequestManager
        +request(method, path, **kwargs) Response
        +get(path, params) Response
        +post(path, json) Response
        +patch(path, json) Response
        +put(path, json) Response
        +delete(path) Response
    }
    class settings {
        <<module>>
        BASE_URL
        API_VERSION
        REQUEST_TIMEOUT
        TOKEN
    }
    class Session {
        <<requests>>
        +headers
        +request()
    }
    class Fixtures {
        <<conftest.py>>
        request_manager()
        github()
        anonymous()
        invalid_client()
        repo_only_client()
        no_admin_client()
    }
    class Helpers {
        <<core/*_helpers.py>>
        create_issue(client, ...)
        create_gist(client, ...)
        create_repo(client, ...)
    }
    GitHubClient "0..*" --> "1" RequestManager : delegates every request
    RequestManager "1" *-- "1" Session : owns
    RequestManager ..> settings : reads config
    GitHubClient ..> settings : default token
    Fixtures ..> GitHubClient : one client per identity
    Fixtures ..> RequestManager : creates and resets
    Helpers ..> GitHubClient : receive a client
```

## Sequence: one request

```mermaid
sequenceDiagram
    participant T as Test
    participant C as GitHubClient (identity)
    participant RM as RequestManager (Singleton)
    participant S as requests.Session
    participant API as api.github.com
    T->>C: github.post(Endpoints.ISSUES, json)
    C->>RM: RequestManager.get_instance()
    RM-->>C: same instance as always
    C->>RM: send("POST", path, token=self.token, json=...)
    RM->>RM: add Authorization: Bearer token (only for this request)
    RM->>S: request(method, BASE_URL + path, headers, timeout)
    S->>API: HTTPS (reused connection)
    API-->>S: 201 Created
    S-->>T: Response
```

## How to use it

```python
from core.api_client import GitHubClient

github = GitHubClient()                 # token from .env
anonymous = GitHubClient(token=None)    # no Authorization header
response = github.get(Endpoints.ISSUES, params={"state": "open"})
```

Tests normally receive the clients from the fixtures (`github`, `anonymous`, `invalid_client`).
Do not create `requests.Session()` or call `requests.get()` in tests or helpers: use a client,
so the request goes through the Singleton. The only exception are the proofs of concept in `tests/poc/`.

The unit tests of the pattern are in `tests/core/test_request_manager.py` and do not need a token:

```
pytest tests/core
```
