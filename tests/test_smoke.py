# ABOUTME: Basic smoke tests to verify the project structure is correct
# ABOUTME: Tests package imports, version, and that all modules are accessible
"""
Basic smoke tests to verify project structure.
"""
import brainplorp
from brainplorp import __version__


def test_version():
    """Test that version is defined."""
    assert __version__ == "1.6.2"


def test_package_imports():
    """Test that main package can be imported."""
    import brainplorp.cli
    import brainplorp.workflows
    import brainplorp.integrations
    import brainplorp.parsers
    import brainplorp.utils

    assert brainplorp.cli is not None
