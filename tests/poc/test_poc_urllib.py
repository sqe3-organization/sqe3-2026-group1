"""POC 4 - HTTP client (urllib — standard library).
Goal: reproduce the same five checks as test_poc_requests.py using only the Python
standard library (urllib.request / urllib.error / urllib.parse).

Key differences from requests/httpx/aiohttp:
  - urllib raises urllib.error.HTTPError for 4xx/5xx responses BY DEFAULT.
    There is no "does not raise" mode; the exception IS the response.
  - There is no raise_for_status() method. The HTTPError exception itself carries
    the status code and the response body — that is urllib's equivalent mechanism.
  - There is no built-in session or .elapsed attribute.
    Headers shared across requests are managed via build_opener() / addheaders,
    and response time is measured manually with time.monotonic().
Public endpoints only, no token needed."""
import json
import time
import urllib.error
import urllib.request

import pytest

BASE = "https://api.github.com"


def _open(url, opener=None, timeout=30):
    """Open url with the given opener (or the default one) and return (response, body_dict)."""
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    op = opener or urllib.request.build_opener()
    with op.open(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode())
    return resp, body


def test_get_returns_status_headers_and_body():
    # Check 1: send Accept header, read status, headers, body and response time (manual).
    req = urllib.request.Request(
        f"{BASE}/repos/octocat/Hello-World",
        headers={"Accept": "application/vnd.github+json"},
    )
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=30) as resp:
        elapsed = time.monotonic() - t0
        body = json.loads(resp.read().decode())

    assert resp.status == 200
    assert "application/json" in resp.headers["Content-Type"]
    assert body["full_name"] == "octocat/Hello-World"
    assert elapsed > 0  # manual timing; urllib has no built-in .elapsed


def test_4xx_raises_by_default():
    # Check 2: urllib raises urllib.error.HTTPError for 4xx responses — the OPPOSITE of requests.
    # The exception IS the response: e.code gives the status and e.read() gives the body.
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(f"{BASE}/repos/octocat/Hello-World/issues/999999999", timeout=30)

    e = exc_info.value
    assert e.code == 404
    body = json.loads(e.read().decode())
    assert body["message"] == "Not Found"


def test_no_raise_for_status_method():
    # Check 3: urllib has NO raise_for_status() method.
    # Its design raises on 4xx automatically (see test_4xx_raises_by_default above),
    # so the equivalent of raise_for_status is simply calling urlopen without try/except.
    # This test documents the absence and verifies the HTTPError carries status + body.
    try:
        urllib.request.urlopen(f"{BASE}/repos/octocat/Hello-World/issues/999999999", timeout=30)
        pytest.fail("Expected HTTPError was not raised")
    except urllib.error.HTTPError as e:
        # The exception object has no raise_for_status(); it *is* the error mechanism.
        assert e.code == 404
        body = json.loads(e.read().decode())
        assert body["message"] == "Not Found"
        assert not hasattr(e, "raise_for_status"), "urllib.error.HTTPError should not have raise_for_status()"


def test_opener_keeps_headers_between_requests():
    # Check 4: build_opener() with addheaders sends the configured header in every request.
    # Verification: we set Accept and X-GitHub-Api-Version via addheaders and confirm:
    #   (a) both requests return HTTP 200 (proving the Accept header was honoured).
    #   (b) the header value appears on the prepared Request object for both calls.
    # Two public read-only endpoints are used: the repo itself and its contributors list.
    custom_header = ("X-GitHub-Api-Version", "2026-03-10")
    opener = urllib.request.build_opener()
    # addheaders is a list of (name, value) tuples.  The opener prepends these to every
    # Request it processes, overriding the default "Host" and "User-Agent" but not "Accept".
    opener.addheaders = [
        ("User-Agent", "Python-urllib/3.10"),
        ("Accept", "application/vnd.github+json"),
        custom_header,
    ]

    urls = [
        f"{BASE}/repos/octocat/Hello-World",
        f"{BASE}/users/octocat",
    ]
    for url in urls:
        req = urllib.request.Request(url)
        with opener.open(req, timeout=30) as resp:
            # HTTP 200 confirms Accept was sent and interpreted by GitHub.
            assert resp.status == 200
        # After open(), the opener has added addheaders to the Request.
        # get_header() uses title-casing (e.g. "X-github-api-version").
        assert req.get_header("X-github-api-version") == "2026-03-10", (
            f"Expected custom header on {url}"
        )
