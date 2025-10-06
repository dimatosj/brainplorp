# ABOUTME: Basic smoke tests to verify the project structure is correct
# ABOUTME: Tests package imports, version, and that all modules are accessible
"""
Basic smoke tests to verify project structure.
"""
import plorp
from plorp import __version__


def test_version():
    """Test that version is defined."""
    assert __version__ == "1.0.0"


def test_package_imports():
    """Test that main package can be imported."""
    import plorp.cli
    import plorp.workflows
    import plorp.integrations
    import plorp.parsers
    import plorp.utils

    assert plorp.cli is not None
