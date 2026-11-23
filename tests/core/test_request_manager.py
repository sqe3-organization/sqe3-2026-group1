"""Unit tests of the RequestManager Singleton (core/request_manager.py).

They do not call GitHub: the session's request method is replaced, so they run without a token.
"""
import logging
import threading

import pytest
import requests

from config import settings
from core.api_client import GitHubClient
from core.logger import FRAMEWORK_LOGGER_NAME
from core.request_manager import MAX_LOGGED_BODY_CHARACTERS, RequestManager

pytestmark = pytest.mark.no_token


def build_fake_response(status_code=200, body=""):
    """A response that was never sent over the network."""
    response = requests.Response()
    response.status_code = status_code
    response._content = body.encode()  # pylint: disable=protected-access
    return response


@pytest.fixture
def sent(monkeypatch):
    """Captures the arguments of every request the RequestManager sends."""
    calls = []

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return build_fake_response()

    monkeypatch.setattr(RequestManager.get_instance().session, "request", fake_request)
    return calls


class MessageCollector(logging.Handler):
    """Keeps the raw messages, before the handlers of the real logger redact them."""

    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


@pytest.fixture
def logged_messages():
    """Messages logged by the framework during a test, at DEBUG level."""
    framework_logger = logging.getLogger(FRAMEWORK_LOGGER_NAME)
    collector = MessageCollector()
    level_before_the_test = framework_logger.level
    framework_logger.setLevel(logging.DEBUG)
    framework_logger.addHandler(collector)
    yield collector.messages
    framework_logger.removeHandler(collector)
    framework_logger.setLevel(level_before_the_test)


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


@pytest.mark.usefixtures("sent")
def test_every_request_is_logged_with_method_path_status_and_duration(logged_messages):
    GitHubClient(token=None).get("/user")

    assert len(logged_messages) == 1
    assert logged_messages[0].startswith("GET /user -> 200 in ")
    assert " ms | auth=anonymous | " in logged_messages[0]


def test_the_token_is_never_logged(sent, logged_messages):
    secret_token = "ghp_secretTokenThatMustNeverBeLogged"

    GitHubClient(token=secret_token).get("/user")

    assert len(sent) == 1
    assert "auth=token" in logged_messages[0]
    assert all(secret_token not in message for message in logged_messages)
    assert all("Authorization" not in message for message in logged_messages)


@pytest.mark.usefixtures("sent")
def test_long_bodies_are_shortened_in_the_log(logged_messages):
    GitHubClient(token=None).post("/gists", json={"content": "x" * 5000})

    assert len(logged_messages[0]) < 5000
    assert f"({len(str({'content': 'x' * 5000}))} characters)" in logged_messages[0]
    assert str(MAX_LOGGED_BODY_CHARACTERS) not in logged_messages[0]


def test_a_failed_connection_is_logged_as_an_error_and_raised(monkeypatch, logged_messages):
    def fail_to_connect(*_args, **_kwargs):
        raise requests.ConnectionError("network unreachable")

    monkeypatch.setattr(RequestManager.get_instance().session, "request", fail_to_connect)

    with pytest.raises(requests.ConnectionError):
        GitHubClient(token=None).get("/user")

    assert logged_messages[0].startswith("GET /user failed after ")
    assert "network unreachable" in logged_messages[0]
