"""Logger of the framework: one format, two outputs (console and a log file per run).

It is built on Python's standard `logging` module, so it adds no dependency.
What it prints is controlled by LOG_LEVEL in .env: a message is shown and written only if
its level is equal to or higher than LOG_LEVEL (DEBUG < INFO < WARNING < ERROR).

Usage in any module of the framework:

    from core.logger import get_logger

    logger = get_logger(__name__)
    logger.info("Label created with name %s", label_name)

The conventions of the team (which level to use and how to word each message)
are in docs/logger-conventions.md.
"""
import logging
import os
import re
import socket
import sys
from datetime import datetime
from pathlib import Path

from config import settings

FRAMEWORK_LOGGER_NAME = "framework"
FILE_ONLY_LOGGER_PREFIX = f"{FRAMEWORK_LOGGER_NAME}.file_only."
VALID_LEVEL_NAMES = ("DEBUG", "INFO", "WARNING", "ERROR")

LOG_FIELD_SEPARATOR = " | "
LOG_LINE_FORMAT = LOG_FIELD_SEPARATOR.join(
    ["%(asctime)s", "%(hostname)s", "%(worker)s", "%(levelname)-7s", "%(message)s"]
)

LOG_FILE_NAME_TEMPLATE = "test_run_{run_id}.log"
RUN_ID_ENVIRONMENT_VARIABLE = "TEST_RUN_ID"
RUN_ID_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

XDIST_WORKER_ENVIRONMENT_VARIABLE = "PYTEST_XDIST_WORKER"
MAIN_PROCESS_NAME = "main"
HOST_NAME = socket.gethostname()

REDACTED_TEXT = "[REDACTED]"
BEARER_TOKEN_PATTERN = re.compile(r"(Bearer\s+)\S+", re.IGNORECASE)
GITHUB_TOKEN_PATTERN = re.compile(r"\b(?:gh[pousr]_|github_pat_)\w+")


def redact_secrets(text):
    """Replaces any bearer token or GitHub token found in the text."""
    text_without_bearer_tokens = BEARER_TOKEN_PATTERN.sub(rf"\1{REDACTED_TEXT}", text)
    return GITHUB_TOKEN_PATTERN.sub(REDACTED_TEXT, text_without_bearer_tokens)


def redact_secrets_in_record(record):
    """Safety net: even if a message includes a token by mistake, it is never written."""
    record.msg = redact_secrets(record.getMessage())
    record.args = ()
    return True


def add_execution_context_to_record(record):
    """Adds the host name and the worker to every record, so lines of different machines
    and of parallel workers (pytest-xdist) can be told apart."""
    record.hostname = HOST_NAME
    record.worker = os.getenv(XDIST_WORKER_ENVIRONMENT_VARIABLE, MAIN_PROCESS_NAME)
    return True

def hide_file_only_records(record):
    """The console skips the records of the loggers created by get_file_only_logger."""
    return not record.name.startswith(FILE_ONLY_LOGGER_PREFIX)

class ConsoleHandler(logging.StreamHandler):
    """Writes to the sys.stdout that is active at the moment of each message.

    pytest replaces sys.stdout while it captures output, so keeping the stream
    that existed at configuration time would write to a closed stream.
    """

    @property
    def stream(self):
        """The stream is looked up on every message instead of being stored."""
        return sys.stdout

    @stream.setter
    def stream(self, _ignored_value):
        """StreamHandler assigns a stream in its constructor; it is ignored on purpose."""


class RunFileHandler(logging.FileHandler):
    """The log file of the run. It has its own class so it can be told apart from the
    capture handlers that pytest also attaches to loggers."""


def parse_level(level_name):
    """Converts "debug" into logging.DEBUG. Fails with a clear message for an unknown level."""
    normalized_name = level_name.upper()
    if normalized_name not in VALID_LEVEL_NAMES:
        valid_levels = ", ".join(VALID_LEVEL_NAMES)
        raise ValueError(f"Invalid LOG_LEVEL '{level_name}'. Use one of: {valid_levels}")
    return logging.getLevelNamesMapping()[normalized_name]


def build_log_file_path(directory):
    """Every run writes to its own file. The run id is shared through an environment variable,
    so the workers of a parallel run (pytest-xdist) append to the same file."""
    run_id = os.environ.setdefault(
        RUN_ID_ENVIRONMENT_VARIABLE, datetime.now().strftime(RUN_ID_TIMESTAMP_FORMAT)
    )
    return Path(directory) / LOG_FILE_NAME_TEMPLATE.format(run_id=run_id)


def attach_team_format(handler, level):
    """Gives a handler the level, the filters and the format shared by the whole team."""
    handler.setLevel(level)
    handler.addFilter(add_execution_context_to_record)
    handler.addFilter(redact_secrets_in_record)
    handler.setFormatter(logging.Formatter(LOG_LINE_FORMAT))
    return handler


def get_framework_handlers():
    """The console and file outputs created by configure_logging.
    pytest attaches its own capture handlers to the same logger, so they are filtered out."""
    return [
        handler
        for handler in logging.getLogger(FRAMEWORK_LOGGER_NAME).handlers
        if isinstance(handler, (ConsoleHandler, RunFileHandler))
    ]


def get_current_log_file():
    """Path of the log file of this run, or None if the logger is not configured yet."""
    for handler in get_framework_handlers():
        if isinstance(handler, RunFileHandler):
            return Path(handler.baseFilename)
    return None


def configure_logging(level_name=None, directory=None):
    """Creates the console and file outputs.
    Calling it again does nothing and returns the file of the first call."""
    current_log_file = get_current_log_file()
    if current_log_file:
        return current_log_file

    level = parse_level(level_name or settings.LOG_LEVEL)
    log_file_path = build_log_file_path(directory or settings.LOG_DIRECTORY)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    framework_logger = logging.getLogger(FRAMEWORK_LOGGER_NAME)
    framework_logger.setLevel(level)
    framework_logger.propagate = False
    console_handler = ConsoleHandler()
    console_handler.addFilter(hide_file_only_records)
    file_handler = RunFileHandler(log_file_path, encoding="utf-8")
    framework_logger.addHandler(attach_team_format(console_handler, level))
    framework_logger.addHandler(attach_team_format(file_handler, level))
    return log_file_path


def shutdown_logging():
    """Flushes and closes both outputs. Used at the end of the run and in unit tests."""
    framework_logger = logging.getLogger(FRAMEWORK_LOGGER_NAME)
    for handler in get_framework_handlers():
        handler.close()
        framework_logger.removeHandler(handler)


def get_logger(module_name):
    """Returns the logger of a module. The first call configures the outputs."""
    configure_logging()
    return logging.getLogger(f"{FRAMEWORK_LOGGER_NAME}.{module_name}")

def get_file_only_logger(module_name):
    """Like get_logger, but its messages are written only to the log file.

    It is used for the life cycle of the run (start and result of each test, fixtures),
    which pytest already shows in the console and would be repeated between its lines.
    """
    return get_logger(f"file_only.{module_name}")