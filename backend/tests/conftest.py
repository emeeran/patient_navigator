"""
Pytest configuration and shared fixtures.
Shared across all test suites.
"""

import pytest


@pytest.fixture
def anyio_backend():
    return "asyncio"
