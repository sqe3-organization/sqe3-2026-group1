"""RequestManager: the single HTTP entry point of the framework (Singleton pattern).

Every test module (Issues, Gists, Repositories, Labels and Milestones) sends its requests
through the same RequestManager instance, so the whole run shares:
- one requests.Session (one connection pool: TCP/TLS connections are reused),
- the base URL, the default headers (Accept, X-GitHub-Api-Version) and the timeout from config.

The token is NOT stored in the Singleton. The auth tests need several identities in the same
run (valid, invalid, anonymous, repo-only, no-admin), so the token travels with each request.
GitHubClient (core/api_client.py) keeps one token and delegates the HTTP call to this class.
"""
import threading

import requests

from config import settings


class RequestManager:
    """Singleton that owns the only requests.Session of the run and sends every request."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        # Double-checked locking: the lock is only taken while the instance does not exist yet
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._setup()
                    cls._instance = instance
        return cls._instance

    @classmethod
    def get_instance(cls):
        """Explicit accessor. RequestManager() returns the same object."""
        return cls()

    @classmethod
    def reset(cls):
        """Closes the session and drops the instance. Used at the end of the run and in unit tests."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.session.close()
                cls._instance = None

    def _setup(self):
        # Runs once per process, not on every RequestManager() call (__init__ would run every time)
        self.base_url = settings.BASE_URL
        self.timeout = settings.REQUEST_TIMEOUT
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": settings.API_VERSION,
        })

    def send(self, method, path, token=None, headers=None, **kwargs):
        """Sends a request to BASE_URL + path. token=None sends it without Authorization.

        requests does not raise on 4xx/5xx, so negative tests can assert the response directly.
        """
        request_headers = dict(headers or {})
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        kwargs.setdefault("timeout", self.timeout)
        return self.session.request(method, f"{self.base_url}{path}", headers=request_headers, **kwargs)
