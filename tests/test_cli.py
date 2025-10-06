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


def test_start_command():
    """Test start command calls daily workflow."""
    from unittest.mock import patch

    runner = CliRunner()

    with patch("plorp.cli.load_config") as mock_load_config:
        with patch("plorp.workflows.daily.start") as mock_daily_start:
            with runner.isolated_filesystem() as temp_dir:
                from pathlib import Path

                vault_path = Path(temp_dir) / "vault"
                vault_path.mkdir()

                mock_load_config.return_value = {"vault_path": str(vault_path)}
                mock_daily_start.return_value = vault_path / "daily" / "2025-10-06.md"

                result = runner.invoke(cli, ["start"])

                assert result.exit_code == 0
                mock_daily_start.assert_called_once()


def test_start_command_file_exists_error():
    """Test start command handles existing file error."""
    from unittest.mock import patch

    runner = CliRunner()

    with patch("plorp.cli.load_config") as mock_load_config:
        with patch("plorp.workflows.daily.start") as mock_daily_start:
            mock_load_config.return_value = {"vault_path": "/tmp/vault"}
            mock_daily_start.side_effect = FileExistsError("❌ Daily note already exists")

            result = runner.invoke(cli, ["start"])

            # Should exit with error
            assert result.exit_code != 0
            assert "already exists" in result.output.lower()


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
