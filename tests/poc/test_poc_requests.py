"""POC 1 - HTTP client (requests).
Goal: call GitHub, send headers and query params, read status/headers/body/time,
and see how 4xx responses are handled. Public endpoints only, no token needed."""
import pytest
import requests

BASE = "https://api.github.com"


def test_get_returns_status_headers_and_body():
    response = requests.get(f"{BASE}/repos/octocat/Hello-World", headers={"Accept": "application/vnd.github+json"}, timeout=30)
    assert response.status_code == 200
    assert "application/json" in response.headers["Content-Type"]
    assert response.json()["full_name"] == "octocat/Hello-World"
    assert response.elapsed.total_seconds() > 0  # response time comes built in


def test_query_params_as_a_dict():
    response = requests.get(f"{BASE}/repos/octocat/Hello-World/issues", params={"state": "all", "per_page": 5}, timeout=30)
    assert response.status_code == 200
    assert len(response.json()) == 5
    assert "per_page=5" in response.url


def test_4xx_does_not_raise_by_default():
    # Unlike Axios (what happened in class with the 404), requests returns the response
    response = requests.get(f"{BASE}/repos/octocat/Hello-World/issues/999999999", timeout=30)
    assert response.status_code == 404
    assert response.json()["message"] == "Not Found"


def test_raise_for_status_raises_on_4xx():
    # raise_for_status() converts the 404 response into an HTTPError exception.
    # This is the opt-in mechanism to get exception-on-error behaviour.
    response = requests.get(f"{BASE}/repos/octocat/Hello-World/issues/999999999", timeout=30)
    with pytest.raises(requests.exceptions.HTTPError):
        response.raise_for_status()


def test_session_keeps_headers_between_requests():
    session = requests.Session()
    session.headers.update({"X-GitHub-Api-Version": "2026-03-10"})
    r1 = session.get(f"{BASE}/repos/octocat/Hello-World", timeout=30)
    r2 = session.get(f"{BASE}/repos/octocat/Hello-World/issues", timeout=30)
    # Both requests must carry the header that was set once on the session.
    assert r1.request.headers["X-GitHub-Api-Version"] == "2026-03-10"
    assert r2.request.headers["X-GitHub-Api-Version"] == "2026-03-10"
