"""Unit tests of the RequestManager Singleton (core/request_manager.py).

They do not call GitHub: the session's request method is replaced, so they run without a token.
"""
import threading

import pytest

from config import settings
from core.api_client import GitHubClient
from core.request_manager import RequestManager

pytestmark = pytest.mark.no_token


@pytest.fixture
def sent(monkeypatch):
    """Captures the arguments of every request the RequestManager sends."""
    calls = []
    manager = RequestManager.get_instance()
    monkeypatch.setattr(manager.session, "request", lambda method, url, **kwargs: calls.append((method, url, kwargs)))
    return calls


def test_constructor_and_accessor_return_the_same_instance():
    assert RequestManager() is RequestManager()
    assert RequestManager.get_instance() is RequestManager()


def test_the_session_is_created_only_once():
    session = RequestManager().session
    RequestManager()
    assert RequestManager().session is session


def test_all_clients_share_the_same_manager_and_session():
    clients = [GitHubClient(), GitHubClient(token=None), GitHubClient(token=settings.INVALID_TOKEN)]
    assert {id(client.manager) for client in clients} == {id(RequestManager.get_instance())}


def test_threads_get_the_same_instance():
    RequestManager.reset()
    instances = []
    threads = [threading.Thread(target=lambda: instances.append(RequestManager())) for _ in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len({id(instance) for instance in instances}) == 1


def test_reset_creates_a_new_instance_on_the_next_call():
    first = RequestManager.get_instance()
    RequestManager.reset()
    assert RequestManager.get_instance() is not first


def test_default_headers_live_in_the_shared_session():
    headers = RequestManager.get_instance().session.headers
    assert headers["Accept"] == "application/vnd.github+json"
    assert headers["X-GitHub-Api-Version"] == settings.API_VERSION
    assert "Authorization" not in headers  # the token is never stored in the Singleton


def test_each_client_sends_its_own_token(sent):
    GitHubClient(token="token-a").get("/user")
    GitHubClient(token=None).get("/user")
    GitHubClient(token="token-b").get("/user")
    auth = [kwargs["headers"].get("Authorization") for _, _, kwargs in sent]
    assert auth == ["Bearer token-a", None, "Bearer token-b"]


def test_url_and_timeout_come_from_config(sent):
    GitHubClient(token=None).post("/gists", json={"a": 1})
    method, url, kwargs = sent[0]
    assert (method, url) == ("POST", f"{settings.BASE_URL}/gists")
    assert kwargs["timeout"] == settings.REQUEST_TIMEOUT
    assert kwargs["json"] == {"a": 1}
