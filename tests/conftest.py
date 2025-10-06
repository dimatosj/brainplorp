# ABOUTME: Pytest configuration file defining shared fixtures for all tests
# ABOUTME: Provides fixtures for test data, sample files, and temporary vault structures
"""
pytest configuration and shared fixtures.
"""
import pytest
from pathlib import Path
import json


@pytest.fixture
def fixture_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_taskwarrior_export(fixture_dir):
    """Load sample TaskWarrior export JSON."""
    with open(fixture_dir / "taskwarrior_export.json") as f:
        return json.load(f)


@pytest.fixture
def sample_daily_note(fixture_dir):
    """Load sample daily note content."""
    with open(fixture_dir / "sample_daily_note.md") as f:
        return f.read()


@pytest.fixture
def sample_inbox(fixture_dir):
    """Load sample inbox content."""
    with open(fixture_dir / "sample_inbox.md") as f:
        return f.read()


@pytest.fixture
def tmp_vault(tmp_path):
    """Create a temporary vault structure."""
    vault = tmp_path / "vault"
    (vault / "daily").mkdir(parents=True)
    (vault / "inbox").mkdir(parents=True)
    (vault / "notes").mkdir(parents=True)
    (vault / "projects").mkdir(parents=True)
    return vault
