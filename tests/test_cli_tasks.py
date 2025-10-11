"""
Tests for the plorp tasks command.
"""
from click.testing import CliRunner
from unittest.mock import patch
import pytest

from brainplorp.cli import cli


@pytest.fixture
def sample_tasks():
    """Sample task data for testing."""
    return [
        {
            'uuid': 'abc-123',
            'description': 'Fix bug',
            'priority': 'H',
            'project': 'work',
            'due': '20251009T000000Z',
            'status': 'pending'
        },
        {
            'uuid': 'def-456',
            'description': 'Review PR',
            'priority': 'M',
            'project': 'work',
            'due': '20251010T000000Z',
            'status': 'pending'
        },
        {
            'uuid': 'ghi-789',
            'description': 'Buy groceries',
            'project': 'home',
            'due': '20251009T000000Z',
            'status': 'pending'
        }
    ]


@patch('brainplorp.cli.load_config')
@patch('brainplorp.cli.get_tasks')
def test_tasks_all_pending(mock_get_tasks, mock_load_config, sample_tasks):
    """Test tasks command shows all pending tasks."""
    mock_load_config.return_value = {'vault_path': '/tmp/vault'}
    mock_get_tasks.return_value = sample_tasks

    runner = CliRunner()
    result = runner.invoke(cli, ['tasks'])

    assert result.exit_code == 0
    assert 'Fix bug' in result.output
    assert 'Review PR' in result.output
    assert 'Buy groceries' in result.output
    mock_get_tasks.assert_called_once_with(['status:pending'])


@patch('brainplorp.cli.load_config')
@patch('brainplorp.cli.get_tasks')
def test_tasks_urgent_only(mock_get_tasks, mock_load_config, sample_tasks):
    """Test tasks --urgent shows only urgent tasks."""
    mock_load_config.return_value = {'vault_path': '/tmp/vault'}
    mock_get_tasks.return_value = [sample_tasks[0]]  # Only urgent task

    runner = CliRunner()
    result = runner.invoke(cli, ['tasks', '--urgent'])

    assert result.exit_code == 0
    assert 'Fix bug' in result.output
    assert 'Review PR' not in result.output
    mock_get_tasks.assert_called_once_with(['status:pending', 'priority:H'])


@patch('brainplorp.cli.load_config')
@patch('brainplorp.cli.get_tasks')
def test_tasks_project_filter(mock_get_tasks, mock_load_config, sample_tasks):
    """Test tasks --project filters by project."""
    mock_load_config.return_value = {'vault_path': '/tmp/vault'}
    mock_get_tasks.return_value = sample_tasks[:2]  # Work tasks

    runner = CliRunner()
    result = runner.invoke(cli, ['tasks', '--project', 'work'])

    assert result.exit_code == 0
    assert 'Fix bug' in result.output
    assert 'Review PR' in result.output
    assert 'Buy groceries' not in result.output
    mock_get_tasks.assert_called_once_with(['status:pending', 'project:work'])


@patch('brainplorp.cli.load_config')
@patch('brainplorp.cli.get_tasks')
def test_tasks_due_today(mock_get_tasks, mock_load_config, sample_tasks):
    """Test tasks --due today filters by due date."""
    mock_load_config.return_value = {'vault_path': '/tmp/vault'}
    mock_get_tasks.return_value = [sample_tasks[0], sample_tasks[2]]

    runner = CliRunner()
    result = runner.invoke(cli, ['tasks', '--due', 'today'])

    assert result.exit_code == 0
    mock_get_tasks.assert_called_once_with(['status:pending', 'due:today'])


@patch('brainplorp.cli.load_config')
@patch('brainplorp.cli.get_tasks')
def test_tasks_overdue(mock_get_tasks, mock_load_config, sample_tasks):
    """Test tasks --overdue shows overdue tasks."""
    mock_load_config.return_value = {'vault_path': '/tmp/vault'}
    mock_get_tasks.return_value = [sample_tasks[0]]

    runner = CliRunner()
    result = runner.invoke(cli, ['tasks', '--due', 'overdue'])

    assert result.exit_code == 0
    mock_get_tasks.assert_called_once_with(['status:pending', 'due.before:today'])


@patch('brainplorp.cli.load_config')
@patch('brainplorp.cli.get_tasks')
def test_tasks_json_format(mock_get_tasks, mock_load_config, sample_tasks):
    """Test tasks --format json outputs JSON."""
    mock_load_config.return_value = {'vault_path': '/tmp/vault'}
    mock_get_tasks.return_value = sample_tasks

    runner = CliRunner()
    result = runner.invoke(cli, ['tasks', '--format', 'json'])

    assert result.exit_code == 0
    import json
    output = json.loads(result.output)
    assert len(output) == 3
    assert output[0]['description'] == 'Fix bug'


@patch('brainplorp.cli.load_config')
@patch('brainplorp.cli.get_tasks')
def test_tasks_simple_format(mock_get_tasks, mock_load_config, sample_tasks):
    """Test tasks --format simple outputs simple format."""
    mock_load_config.return_value = {'vault_path': '/tmp/vault'}
    mock_get_tasks.return_value = sample_tasks

    runner = CliRunner()
    result = runner.invoke(cli, ['tasks', '--format', 'simple'])

    assert result.exit_code == 0
    assert '[H] Fix bug (work)' in result.output
    assert '[M] Review PR (work)' in result.output


@patch('brainplorp.cli.load_config')
@patch('brainplorp.cli.get_tasks')
def test_tasks_combine_filters(mock_get_tasks, mock_load_config, sample_tasks):
    """Test combining multiple filters."""
    mock_load_config.return_value = {'vault_path': '/tmp/vault'}
    mock_get_tasks.return_value = [sample_tasks[0]]

    runner = CliRunner()
    result = runner.invoke(cli, ['tasks', '--urgent', '--project', 'work'])

    assert result.exit_code == 0
    mock_get_tasks.assert_called_once_with(['status:pending', 'priority:H', 'project:work'])


@patch('brainplorp.cli.load_config')
@patch('brainplorp.cli.get_tasks')
def test_tasks_limit(mock_get_tasks, mock_load_config, sample_tasks):
    """Test tasks --limit restricts results."""
    mock_load_config.return_value = {'vault_path': '/tmp/vault'}
    mock_get_tasks.return_value = sample_tasks

    runner = CliRunner()
    result = runner.invoke(cli, ['tasks', '--limit', '2'])

    assert result.exit_code == 0
    # Should only show first 2 tasks
    assert result.output.count('│') >= 2  # At least 2 rows in table


@patch('brainplorp.cli.load_config')
@patch('brainplorp.cli.get_tasks')
def test_tasks_empty_result(mock_get_tasks, mock_load_config):
    """Test tasks command with no results."""
    mock_load_config.return_value = {'vault_path': '/tmp/vault'}
    mock_get_tasks.return_value = []

    runner = CliRunner()
    result = runner.invoke(cli, ['tasks'])

    assert result.exit_code == 0
    assert 'Tasks (0)' in result.output


def test_format_date_today():
    """Test format_date for today's date."""
    from brainplorp.utils.dates import format_date
    from datetime import datetime

    today = datetime.now().strftime('%Y%m%dT000000Z')
    result = format_date(today, 'short')
    assert result == 'today'


def test_format_date_iso():
    """Test format_date ISO format."""
    from brainplorp.utils.dates import format_date

    result = format_date('20251009T000000Z', 'iso')
    assert result == '2025-10-09'


def test_format_date_empty():
    """Test format_date with empty string."""
    from brainplorp.utils.dates import format_date

    result = format_date('', 'short')
    assert result == ''
