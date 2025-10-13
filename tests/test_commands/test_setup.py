# ABOUTME: Tests for brainplorp setup wizard command
# ABOUTME: Covers vault detection, config generation, and MCP configuration

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from click.testing import CliRunner
import json
import yaml

from brainplorp.commands.setup import (
    setup,
    detect_obsidian_vault,
    configure_mcp,
    which_command
)


class TestDetectObsidianVault:
    """Test vault detection logic."""

    def test_detects_icloud_vault(self, tmp_path):
        """Should detect vault in iCloud Drive."""
        # Create mock iCloud path structure
        icloud_path = tmp_path / 'Library' / 'Mobile Documents' / 'iCloud~md~obsidian' / 'MyVault'
        icloud_path.mkdir(parents=True)
        (icloud_path / '.obsidian').mkdir()

        with patch('brainplorp.commands.setup.Path.home', return_value=tmp_path):
            result = detect_obsidian_vault()
            assert result == icloud_path

    def test_detects_documents_vault(self, tmp_path):
        """Should detect vault in Documents/Obsidian Vaults."""
        vault_path = tmp_path / 'Documents' / 'Obsidian Vaults' / 'MyVault'
        vault_path.mkdir(parents=True)
        (vault_path / '.obsidian').mkdir()

        # Create iCloud path but don't populate it
        icloud_path = tmp_path / 'Library' / 'Mobile Documents' / 'iCloud~md~obsidian'
        icloud_path.mkdir(parents=True)

        with patch('brainplorp.commands.setup.Path.home', return_value=tmp_path):
            result = detect_obsidian_vault()
            assert result == vault_path

    def test_detects_home_vault(self, tmp_path):
        """Should detect vault in ~/vault."""
        vault_path = tmp_path / 'vault'
        vault_path.mkdir()
        (vault_path / '.obsidian').mkdir()

        with patch('brainplorp.commands.setup.Path.home', return_value=tmp_path):
            result = detect_obsidian_vault()
            assert result == vault_path

    def test_returns_none_when_no_vault(self, tmp_path):
        """Should return None when no vault detected."""
        with patch('brainplorp.commands.setup.Path.home', return_value=tmp_path):
            result = detect_obsidian_vault()
            assert result is None


class TestWhichCommand:
    """Test command path detection."""

    def test_finds_existing_command(self):
        """Should find command in PATH."""
        with patch('shutil.which', return_value='/usr/bin/task'):
            result = which_command('task')
            assert result == Path('/usr/bin/task')

    def test_returns_none_for_missing_command(self):
        """Should return None for missing command."""
        with patch('shutil.which', return_value=None):
            result = which_command('nonexistent')
            assert result is None


class TestConfigureMCP:
    """Test Claude Desktop MCP configuration."""

    def test_skips_when_claude_not_installed(self, capsys):
        """Should skip gracefully when Claude Desktop not found."""
        with patch('brainplorp.commands.setup.Path.home') as mock_home:
            mock_home.return_value = Path('/nonexistent')
            configure_mcp()

            captured = capsys.readouterr()
            assert "Claude Desktop config not found" in captured.out

    def test_configures_mcp_when_claude_exists(self, tmp_path):
        """Should add brainplorp to mcpServers."""
        claude_config_path = tmp_path / 'Library' / 'Application Support' / 'Claude' / 'claude_desktop_config.json'
        claude_config_path.parent.mkdir(parents=True)

        # Create existing config
        existing_config = {'mcpServers': {'other': {'command': '/bin/other'}}}
        claude_config_path.write_text(json.dumps(existing_config))

        with patch('brainplorp.commands.setup.Path.home', return_value=tmp_path):
            with patch('brainplorp.commands.setup.which_command', return_value=Path('/usr/local/bin/brainplorp-mcp')):
                configure_mcp()

        # Verify backup created
        backup_path = claude_config_path.parent / 'claude_desktop_config.json.backup'
        assert backup_path.exists()

        # Verify brainplorp added
        updated_config = json.loads(claude_config_path.read_text())
        assert 'brainplorp' in updated_config['mcpServers']
        assert updated_config['mcpServers']['brainplorp']['command'] == '/usr/local/bin/brainplorp-mcp'
        assert 'other' in updated_config['mcpServers']  # Existing server preserved


class TestSetupCommand:
    """Test setup wizard CLI command."""

    def test_setup_command_creates_config(self, tmp_path):
        """Should create config file with user inputs."""
        runner = CliRunner()

        with patch('brainplorp.commands.setup.Path.home', return_value=tmp_path):
            with patch('brainplorp.commands.setup.detect_obsidian_vault', return_value=None):
                with patch('brainplorp.commands.setup.check_taskwarrior', return_value={'passed': True, 'message': 'TaskWarrior OK'}):
                    with patch('brainplorp.commands.setup.configure_mcp'):
                        # Simulate user inputs
                        result = runner.invoke(setup, input=(
                            '/Users/test/vault\n'  # vault path
                            'n\n'  # skip TaskWarrior sync
                            'vim\n'  # editor
                            'n\n'  # skip email
                            'n\n'  # skip vault sync
                            'n\n'  # skip MCP
                        ))

                        assert result.exit_code == 0
                        assert '✅ Setup complete!' in result.output

                        # Verify config created
                        config_path = tmp_path / '.config' / 'brainplorp' / 'config.yaml'
                        assert config_path.exists()

                        config = yaml.safe_load(config_path.read_text())
                        assert config['vault_path'] == '/Users/test/vault'
                        assert config['default_editor'] == 'vim'
                        assert config['email']['enabled'] is False

    def test_setup_accepts_detected_vault(self, tmp_path):
        """Should use detected vault when user confirms."""
        runner = CliRunner()
        detected_vault = tmp_path / 'vault'

        with patch('brainplorp.commands.setup.Path.home', return_value=tmp_path):
            with patch('brainplorp.commands.setup.detect_obsidian_vault', return_value=detected_vault):
                with patch('brainplorp.commands.setup.check_taskwarrior', return_value={'passed': True, 'message': 'TaskWarrior OK'}):
                    with patch('brainplorp.commands.setup.configure_mcp'):
                        result = runner.invoke(setup, input=(
                            'y\n'  # use detected vault
                            'n\n'  # skip TaskWarrior sync
                            'vim\n'  # editor
                            'n\n'  # skip email
                            'n\n'  # skip vault sync
                            'n\n'  # skip MCP
                        ))

                        assert result.exit_code == 0
                        config_path = tmp_path / '.config' / 'brainplorp' / 'config.yaml'
                        config = yaml.safe_load(config_path.read_text())
                        assert config['vault_path'] == str(detected_vault)

    def test_setup_configures_email(self, tmp_path):
        """Should configure email when user opts in."""
        runner = CliRunner()

        with patch('brainplorp.commands.setup.Path.home', return_value=tmp_path):
            with patch('brainplorp.commands.setup.detect_obsidian_vault', return_value=None):
                with patch('brainplorp.commands.setup.check_taskwarrior', return_value={'passed': True, 'message': 'TaskWarrior OK'}):
                    with patch('brainplorp.commands.setup.configure_mcp'):
                        result = runner.invoke(setup, input=(
                            '/Users/test/vault\n'  # vault path
                            'n\n'  # skip TaskWarrior sync
                            'vim\n'  # editor
                            'y\n'  # configure email
                            'user@gmail.com\n'  # email
                            'app-password-here\n'  # password
                            'work\n'  # label
                            'n\n'  # skip vault sync
                            'n\n'  # skip MCP
                        ))

                        assert result.exit_code == 0
                        config_path = tmp_path / '.config' / 'brainplorp' / 'config.yaml'
                        config = yaml.safe_load(config_path.read_text())
                        assert config['email']['enabled'] is True
                        assert config['email']['username'] == 'user@gmail.com'
                        assert config['email']['inbox_label'] == 'work'
