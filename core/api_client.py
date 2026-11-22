"""API client for the GitHub REST API.

A GitHubClient represents one identity (a token, or none for anonymous requests).
It does not open connections itself: every call goes through the RequestManager Singleton
(core/request_manager.py), which owns the only requests.Session of the run.
"""
from config import settings
from core.request_manager import RequestManager

_DEFAULT = object()


class GitHubClient:
    """One identity (token or anonymous). The HTTP call is delegated to the RequestManager."""

    def __init__(self, token=_DEFAULT):
        """token: defaults to the one in .env. Pass None to send requests without Authorization."""
        self.token = settings.TOKEN if token is _DEFAULT else token

    @property
    def manager(self):
        """Looked up on every call (not stored), so a client never keeps a closed session after a reset."""
        return RequestManager.get_instance()

    def request(self, method, path, **kwargs):
        """Sends any method with this client's token."""
        return self.manager.send(method, path, token=self.token, **kwargs)

    def get(self, path, params=None):
        """GET with optional query params."""
        return self.request("GET", path, params=params)

    def post(self, path, json=None):
        """POST with a JSON body."""
        return self.request("POST", path, json=json)

    def patch(self, path, json=None):
        """PATCH with a JSON body."""
        return self.request("PATCH", path, json=json)

    def put(self, path, json=None):
        """PUT with a JSON body."""
        return self.request("PUT", path, json=json)

    def delete(self, path):
        """DELETE."""
        return self.request("DELETE", path)
