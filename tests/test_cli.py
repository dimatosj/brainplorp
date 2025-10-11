# ABOUTME: Tests for the CLI interface - validates commands, help text, and version output
# ABOUTME: Uses Click's CliRunner to test command behavior without actually running plorp
"""
CLI smoke tests.
"""
from unittest.mock import patch
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
    assert "1.5.2" in result.output


def test_start_command():
    """Test start command calls start_day core function."""
    from unittest.mock import patch

    runner = CliRunner()

    with patch("plorp.cli.load_config") as mock_load_config:
        with patch("plorp.cli.start_day") as mock_start_day:
            with runner.isolated_filesystem() as temp_dir:
                from pathlib import Path

                vault_path = Path(temp_dir) / "vault"
                vault_path.mkdir()

                note_path = str(vault_path / "daily" / "2025-10-06.md")
                mock_load_config.return_value = {"vault_path": str(vault_path)}
                mock_start_day.return_value = {
                    "note_path": note_path,
                    "summary": {
                        "overdue_count": 0,
                        "due_today_count": 2,
                        "recurring_count": 1,
                        "total_count": 3,
                    },
                }

                result = runner.invoke(cli, ["start"])

                assert result.exit_code == 0
                mock_start_day.assert_called_once()


def test_start_command_file_exists_error():
    """Test start command handles existing file error."""
    from unittest.mock import patch
    from plorp.core.exceptions import DailyNoteExistsError

    runner = CliRunner()

    with patch("plorp.cli.load_config") as mock_load_config:
        with patch("plorp.cli.start_day") as mock_start_day:
            mock_load_config.return_value = {"vault_path": "/tmp/vault"}
            mock_start_day.side_effect = DailyNoteExistsError(
                "2025-10-06", "/tmp/vault/daily/2025-10-06.md"
            )

            result = runner.invoke(cli, ["start"])

            # Should exit with error
            assert result.exit_code != 0
            assert "already exists" in result.output.lower()


# Sprint 3: Review command tests


@patch("plorp.cli.load_config")
@patch("plorp.cli.get_review_tasks")
@patch("plorp.cli.add_review_notes")
@patch("plorp.cli.prompt")
def test_review_command(mock_prompt, mock_add_notes, mock_get_tasks, mock_load_config, tmp_path):
    """Test review command with no uncompleted tasks."""
    mock_load_config.return_value = {"vault_path": str(tmp_path)}
    mock_get_tasks.return_value = {
        "date": "2025-10-06",
        "note_path": str(tmp_path / "daily" / "2025-10-06.md"),
        "uncompleted_tasks": [],
        "uncompleted_count": 0,
    }
    mock_prompt.return_value = "Test reflection"

    runner = CliRunner()
    result = runner.invoke(cli, ["review"])

    assert result.exit_code == 0
    assert "All tasks completed" in result.output
    mock_get_tasks.assert_called_once()


@patch("plorp.cli.load_config")
@patch("plorp.cli.get_review_tasks")
def test_review_command_keyboard_interrupt(mock_get_tasks, mock_load_config):
    """Test review command handles keyboard interrupt."""
    mock_load_config.return_value = {"vault_path": "/tmp/vault"}
    mock_get_tasks.side_effect = KeyboardInterrupt()

    runner = CliRunner()
    result = runner.invoke(cli, ["review"])

    # Should exit gracefully
    assert result.exit_code == 0
    assert "interrupted" in result.output.lower()


# Inbox command tests (Sprint 4)


@patch("plorp.cli.load_config")
@patch("plorp.cli.get_inbox_items")
def test_inbox_command(mock_get_inbox, mock_load_config, tmp_path):
    """Test inbox command with empty inbox."""
    from click.testing import CliRunner
    from plorp.cli import cli

    mock_load_config.return_value = {"vault_path": str(tmp_path)}
    mock_get_inbox.return_value = {
        "inbox_path": str(tmp_path / "inbox" / "2025-10.md"),
        "unprocessed_items": [],
        "item_count": 0,
    }

    runner = CliRunner()
    result = runner.invoke(cli, ["inbox", "process"])

    assert result.exit_code == 0
    assert "empty" in result.output.lower()
    mock_get_inbox.assert_called_once()


def test_inbox_command_invalid_subcommand():
    """Test inbox command with invalid subcommand."""
    from click.testing import CliRunner
    from plorp.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["inbox", "invalid"])

    assert result.exit_code == 1
    assert "Unknown" in result.output


@patch("plorp.cli.load_config")
@patch("plorp.cli.get_inbox_items")
def test_inbox_command_keyboard_interrupt(mock_get_inbox, mock_load_config):
    """Test inbox command handles keyboard interrupt."""
    mock_load_config.return_value = {"vault_path": "/tmp/vault"}
    mock_get_inbox.side_effect = KeyboardInterrupt()

    from click.testing import CliRunner
    from plorp.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["inbox", "process"])

    # Should exit gracefully
    assert result.exit_code == 0
    assert "interrupted" in result.output.lower()


# Note and link command tests (Sprint 5)


@patch("plorp.cli.load_config")
@patch("plorp.cli.create_note_standalone")
def test_note_command(mock_create_note, mock_load_config, tmp_path):
    """Test note command creates note without task link."""
    note_path = str(tmp_path / "notes" / "test-note.md")

    mock_load_config.return_value = {"vault_path": str(tmp_path)}
    mock_create_note.return_value = {"note_path": note_path}

    runner = CliRunner()
    result = runner.invoke(cli, ["note", "Test Note"])

    assert result.exit_code == 0
    assert "Created note" in result.output
    assert "test-note.md" in result.output
    mock_create_note.assert_called_once()


@patch("plorp.cli.load_config")
@patch("plorp.cli.create_note_linked_to_task")
def test_note_command_with_task(mock_create_note, mock_load_config, tmp_path):
    """Test note command creates note with task link."""
    note_path = str(tmp_path / "notes" / "test-note.md")

    mock_load_config.return_value = {"vault_path": str(tmp_path)}
    mock_create_note.return_value = {
        "note_path": note_path,
        "task_uuid": "abc-123",
        "linked": True,
    }

    runner = CliRunner()
    result = runner.invoke(cli, ["note", "Test Note", "--task", "abc-123"])

    assert result.exit_code == 0
    assert "Created note" in result.output
    assert "Linked to task" in result.output
    mock_create_note.assert_called_once()


@patch("plorp.cli.load_config")
@patch("plorp.cli.link_note_to_task")
def test_link_command(mock_link_note, mock_load_config, tmp_path):
    """Test link command links existing note to task."""
    vault = tmp_path / "vault"
    note_path = vault / "notes" / "existing-note.md"

    mock_load_config.return_value = {"vault_path": str(vault)}
    mock_link_note.return_value = {
        "note_path": str(note_path),
        "task_uuid": "abc-123",
        "linked": True,
    }

    runner = CliRunner()
    result = runner.invoke(cli, ["link", "abc-123", str(note_path)])

    assert result.exit_code == 0
    assert "Linked" in result.output
    mock_link_note.assert_called_once()


@patch("plorp.cli.load_config")
@patch("plorp.cli.link_note_to_task")
def test_link_command_note_not_found(mock_link_note, mock_load_config, tmp_path):
    """Test link command handles non-existent note."""
    vault = tmp_path / "vault"

    mock_load_config.return_value = {"vault_path": str(vault)}
    mock_link_note.side_effect = FileNotFoundError("Note not found")

    runner = CliRunner()
    result = runner.invoke(cli, ["link", "abc-123", str(vault / "nonexistent.md")])

    # Should exit with error
    assert result.exit_code != 0
    assert "error" in result.output.lower()
