# ABOUTME: Tests for the CLI interface - validates commands, help text, and version output
# ABOUTME: Uses Click's CliRunner to test command behavior without actually running plorp
"""
CLI smoke tests.
"""
from click.testing import CliRunner
from plorp.cli import cli


def test_cli_help():
    """Test that CLI help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "plorp" in result.output
    assert "Workflow automation" in result.output


def test_cli_version():
    """Test that version flag works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert "1.0.0" in result.output


def test_start_stub():
    """Test that start command shows not implemented message."""
    runner = CliRunner()
    result = runner.invoke(cli, ["start"])

    assert result.exit_code == 0
    assert "not yet implemented" in result.output
    assert "future sprint" in result.output


def test_review_stub():
    """Test that review command shows not implemented message."""
    runner = CliRunner()
    result = runner.invoke(cli, ["review"])

    assert result.exit_code == 0
    assert "not yet implemented" in result.output


def test_inbox_stub():
    """Test that inbox command shows not implemented message."""
    runner = CliRunner()
    result = runner.invoke(cli, ["inbox"])

    assert result.exit_code == 0
    assert "not yet implemented" in result.output
