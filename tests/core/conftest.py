"""Fixtures shared by the unit tests of the framework (tests/core)."""
import logging

import pytest

from core.logger import (
    FRAMEWORK_LOGGER_NAME,
    RUN_ID_ENVIRONMENT_VARIABLE,
    get_framework_handlers,
    shutdown_logging,
)


@pytest.fixture(autouse=True)
def isolated_logging(monkeypatch):
    """Keeps the unit tests out of the log of the real run.

    The outputs of the run are detached while a unit test runs, so the requests and errors
    that the unit tests simulate never reach the log file (and never reach its report).
    Each test that needs an output creates its own one in a temporary folder.
    """
    framework_logger = logging.getLogger(FRAMEWORK_LOGGER_NAME)
    handlers_of_the_run = get_framework_handlers()
    level_of_the_run = framework_logger.level
    for handler in handlers_of_the_run:
        framework_logger.removeHandler(handler)
    monkeypatch.setenv(RUN_ID_ENVIRONMENT_VARIABLE, "unit_test_run")
    yield
    shutdown_logging()
    for handler in handlers_of_the_run:
        framework_logger.addHandler(handler)
    framework_logger.setLevel(level_of_the_run)