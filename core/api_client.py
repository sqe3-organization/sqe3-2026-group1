"""API client for the GitHub REST API.

Replaces the collection-level auth and pre-request script of the Postman collection:
base URL, Accept and X-GitHub-Api-Version headers, and the Bearer token.
"""
import requests

from config import settings

_DEFAULT = object()


class GitHubClient:
    def __init__(self, token=_DEFAULT):
        """token: defaults to the one in .env. Pass None to send requests without Authorization."""
        token = settings.TOKEN if token is _DEFAULT else token
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": settings.API_VERSION,
        })
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def request(self, method, path, **kwargs):
        # requests does not raise on 4xx/5xx, so negative tests can assert the response directly
        return self.session.request(method, f"{settings.BASE_URL}{path}", timeout=30, **kwargs)

    def get(self, path, params=None):
        return self.request("GET", path, params=params)

    def post(self, path, json=None):
        return self.request("POST", path, json=json)

    def patch(self, path, json=None):
        return self.request("PATCH", path, json=json)

    def put(self, path, json=None):
        return self.request("PUT", path, json=json)

    def delete(self, path):
        return self.request("DELETE", path)
