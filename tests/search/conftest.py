"""Fixtures of the Search tests (tests/search/conftest.py).

The Search API is read-only: no resource is created or deleted by these tests.
All fixtures are session-scoped because a single client is enough for all tests.
"""
import pytest

from config import settings


# The github, anonymous and invalid_client fixtures come from the global conftest.
# No additional fixtures are needed: Search is a read-only API.
