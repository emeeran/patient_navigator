"""
Pytest configuration for data schema validation tests.
Provides shared fixtures for loading JSON Schema files from specs/data/.
"""

import json
from pathlib import Path

import pytest

# Base path to schema files (relative to project root)
SCHEMAS_DIR = Path(__file__).resolve().parents[4] / "specs" / "data"


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "spec(spec_id): trace test back to a spec ID in REGISTRY.md"
    )


@pytest.fixture
def load_schema():
    """
    Fixture that returns a callable to load a JSON Schema from specs/data/.
    Caches loaded schemas for reuse within a session.
    """
    _cache = {}

    def _load(filename: str) -> dict:
        if filename in _cache:
            return _cache[filename]
        schema_path = SCHEMAS_DIR / filename
        with open(schema_path, encoding="utf-8") as f:
            schema = json.load(f)
        _cache[filename] = schema
        return schema

    return _load
