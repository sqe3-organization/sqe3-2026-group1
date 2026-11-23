"""Unit tests of the logger (core/logger.py).

They do not call GitHub: they only write to a temporary folder, so they run without a token.
"""
import re

import pytest

from core.logger import (
    XDIST_WORKER_ENVIRONMENT_VARIABLE,
    configure_logging,
    get_file_only_logger,
    get_framework_handlers,
    get_logger,
    shutdown_logging,
)

pytestmark = pytest.mark.no_token

TEAM_LOG_LINE_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} \| \S+ \| \S+ \| (DEBUG|INFO|WARNING|ERROR)\s* \| .+$"
)


def read_log_file(log_file_path):
    return log_file_path.read_text(encoding="utf-8")


def test_log_file_is_created_in_the_given_directory(tmp_path):
    log_file_path = configure_logging("INFO", tmp_path)

    assert log_file_path.parent == tmp_path
    assert log_file_path.name == "test_run_unit_test_run.log"


def test_every_line_follows_the_team_format(tmp_path):
    log_file_path = configure_logging("INFO", tmp_path)

    get_logger("unit_test").info("Label created with name qa-pm-label")
    shutdown_logging()

    assert TEAM_LOG_LINE_PATTERN.match(read_log_file(log_file_path).strip())


def test_info_level_hides_debug_messages(tmp_path):
    log_file_path = configure_logging("INFO", tmp_path)

    get_logger("unit_test").debug("request detail")
    get_logger("unit_test").info("business message")
    shutdown_logging()

    content = read_log_file(log_file_path)
    assert "request detail" not in content
    assert "business message" in content


def test_debug_level_shows_debug_messages(tmp_path):
    log_file_path = configure_logging("DEBUG", tmp_path)

    get_logger("unit_test").debug("request detail")
    shutdown_logging()

    assert "request detail" in read_log_file(log_file_path)


def test_the_console_receives_the_same_messages(tmp_path, capsys):
    configure_logging("INFO", tmp_path)

    get_logger("unit_test").warning("cleanup found the resource already deleted")

    assert "cleanup found the resource already deleted" in capsys.readouterr().out


def test_the_level_also_filters_the_console(tmp_path, capsys):
    configure_logging("WARNING", tmp_path)

    get_logger("unit_test").info("business message")

    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    "message_with_secret",
    [
        "Authorization: Bearer ghp_abcdefghijklmnopqrstuvwxyz0123456789",
        "token used: github_pat_11ABCDEFG0123456789_abcdefghijklmnop",
        "token used: ghp_abcdefghijklmnopqrstuvwxyz0123456789",
    ],
)
def test_tokens_are_never_written(tmp_path, capsys, message_with_secret):
    log_file_path = configure_logging("DEBUG", tmp_path)

    get_logger("unit_test").debug(message_with_secret)
    shutdown_logging()

    secret = message_with_secret.split()[-1]
    assert secret not in read_log_file(log_file_path)
    assert secret not in capsys.readouterr().out
    assert "[REDACTED]" in read_log_file(log_file_path)


def test_the_worker_is_taken_from_the_xdist_variable(tmp_path, monkeypatch):
    monkeypatch.setenv(XDIST_WORKER_ENVIRONMENT_VARIABLE, "gw3")
    log_file_path = configure_logging("INFO", tmp_path)

    get_logger("unit_test").info("message from a worker")
    shutdown_logging()

    assert " | gw3 | " in read_log_file(log_file_path)


def test_the_worker_is_main_when_the_run_is_not_parallel(tmp_path, monkeypatch):
    monkeypatch.delenv(XDIST_WORKER_ENVIRONMENT_VARIABLE, raising=False)
    log_file_path = configure_logging("INFO", tmp_path)

    get_logger("unit_test").info("message from the main process")
    shutdown_logging()

    assert " | main | " in read_log_file(log_file_path)


def test_configuring_twice_does_not_duplicate_the_outputs(tmp_path):
    first_log_file_path = configure_logging("INFO", tmp_path)
    second_log_file_path = configure_logging("DEBUG", tmp_path)

    assert second_log_file_path == first_log_file_path
    assert len(get_framework_handlers()) == 2


def test_an_unknown_level_is_rejected_with_a_clear_message(tmp_path):
    with pytest.raises(ValueError, match="Invalid LOG_LEVEL 'LOUD'"):
        configure_logging("LOUD", tmp_path)


def test_a_file_only_logger_writes_to_the_file_but_not_to_the_console(tmp_path, capsys):
    log_file_path = configure_logging("INFO", tmp_path)

    get_file_only_logger("unit_test").info("START tests/issues/test_post.py::test_create")
    get_logger("unit_test").info("business message")
    shutdown_logging()

    assert "START tests/issues/test_post.py::test_create" in read_log_file(log_file_path)
    console_output = capsys.readouterr().out
    assert "START" not in console_output
    assert "business message" in console_output

def test_a_file_only_logger_writes_to_the_file_but_not_to_the_console(tmp_path, capsys):
    log_file_path = configure_logging("INFO", tmp_path)

    get_file_only_logger("unit_test").info("START tests/issues/test_post.py::test_create")
    get_logger("unit_test").info("business message")
    shutdown_logging()

    assert "START tests/issues/test_post.py::test_create" in read_log_file(log_file_path)
    console_output = capsys.readouterr().out
    assert "START" not in console_output
    assert "business message" in console_output