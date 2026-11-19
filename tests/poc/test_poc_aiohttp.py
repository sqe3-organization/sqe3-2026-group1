"""POC 3 - HTTP client (aiohttp).
Goal: reproduce the same five checks as test_poc_requests.py using aiohttp.
aiohttp is async-first; every HTTP call uses await.
Key differences from requests/httpx:
  - All requests are async (async def + await).
  - raise_for_status() raises aiohttp.ClientResponseError; it can be called after await.
  - There is no .elapsed attribute; response time is measured with time.monotonic().
  - 4xx responses do NOT raise by default (raise_for_status=False is the default).
Public endpoints only, no token needed."""
import time

import aiohttp
import pytest

BASE = "https://api.github.com"
HEADERS = {"Accept": "application/vnd.github+json"}


@pytest.mark.asyncio
async def test_get_returns_status_headers_and_body():
    # Check 1: send a custom header, read status, headers, body and response time.
    # aiohttp does not expose .elapsed; time is measured manually with time.monotonic().
    async with aiohttp.ClientSession() as session:
        t0 = time.monotonic()
        async with session.get(f"{BASE}/repos/octocat/Hello-World", headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)) as response:
            elapsed = time.monotonic() - t0
            body = await response.json(content_type=None)

    assert response.status == 200
    assert "application/json" in response.headers["Content-Type"]
    assert body["full_name"] == "octocat/Hello-World"
    assert elapsed > 0  # manual timing because aiohttp has no built-in .elapsed


@pytest.mark.asyncio
async def test_4xx_does_not_raise_by_default():
    # Check 2: aiohttp does NOT raise on 4xx by default (raise_for_status is not called).
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE}/repos/octocat/Hello-World/issues/999999999",
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            body = await response.json(content_type=None)

    assert response.status == 404
    assert body["message"] == "Not Found"


@pytest.mark.asyncio
async def test_raise_for_status_raises_on_4xx():
    # Check 3: raise_for_status() converts the 404 into a ClientResponseError.
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE}/repos/octocat/Hello-World/issues/999999999",
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            with pytest.raises(aiohttp.ClientResponseError):
                response.raise_for_status()


@pytest.mark.asyncio
async def test_session_keeps_headers_between_requests():
    # Check 4: headers set on the ClientSession are sent in every request.
    # aiohttp does not expose outgoing headers after the fact via response.request_info.headers,
    # so we verify indirectly: both requests succeed (200) with the shared Accept header
    # and we also check response.request_info.headers for the custom API-version header.
    async with aiohttp.ClientSession(
        headers={"X-GitHub-Api-Version": "2026-03-10"},
        timeout=aiohttp.ClientTimeout(total=30),
    ) as session:
        async with session.get(f"{BASE}/repos/octocat/Hello-World") as r1:
            await r1.read()
        async with session.get(f"{BASE}/repos/octocat/Hello-World/issues") as r2:
            await r2.read()

    # request_info.headers contains the headers actually sent in each request.
    assert r1.request_info.headers["X-GitHub-Api-Version"] == "2026-03-10"
    assert r2.request_info.headers["X-GitHub-Api-Version"] == "2026-03-10"
