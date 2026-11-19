"""POC 2 - HTTP client (httpx).
Goal: reproduce the same five checks as test_poc_requests.py using httpx.
httpx has an API almost identical to requests; the key differences are:
  - httpx.Client() is the session equivalent (used as a context manager).
  - raise_for_status() raises httpx.HTTPStatusError instead of requests.HTTPError.
  - response.elapsed is available, same as requests.
Public endpoints only, no token needed."""
import pytest
import httpx

BASE = "https://api.github.com"


def test_get_returns_status_headers_and_body():
    # Check 1: send a custom header, read status, headers, body and response time.
    response = httpx.get(f"{BASE}/repos/octocat/Hello-World", headers={"Accept": "application/vnd.github+json"}, timeout=30)
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]  # httpx lowercases header names
    assert response.json()["full_name"] == "octocat/Hello-World"
    assert response.elapsed.total_seconds() > 0  # httpx exposes elapsed just like requests


def test_4xx_does_not_raise_by_default():
    # Check 2: a 404 response is returned normally, no exception is raised.
    response = httpx.get(f"{BASE}/repos/octocat/Hello-World/issues/999999999", timeout=30)
    assert response.status_code == 404
    assert response.json()["message"] == "Not Found"


def test_raise_for_status_raises_on_4xx():
    # Check 3: raise_for_status() converts the 404 into an HTTPStatusError.
    response = httpx.get(f"{BASE}/repos/octocat/Hello-World/issues/999999999", timeout=30)
    with pytest.raises(httpx.HTTPStatusError):
        response.raise_for_status()


def test_client_keeps_headers_between_requests():
    # Check 4: httpx.Client() is the session equivalent.
    # Headers set on the client are sent in every request made through it.
    with httpx.Client(headers={"X-GitHub-Api-Version": "2026-03-10"}, timeout=30) as client:
        r1 = client.get(f"{BASE}/repos/octocat/Hello-World")
        r2 = client.get(f"{BASE}/repos/octocat/Hello-World/issues")
        # Verify the custom header was present in both outgoing requests.
        assert r1.request.headers["x-github-api-version"] == "2026-03-10"
        assert r2.request.headers["x-github-api-version"] == "2026-03-10"
