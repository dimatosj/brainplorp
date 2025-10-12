# ABOUTME: Interactive setup wizard for brainplorp first-time configuration
# ABOUTME: Detects Obsidian vault, configures TaskWarrior sync, email, and Claude Desktop MCP

import click
import os
from pathlib import Path
import json
import yaml
import shutil


@click.command()
def setup():
    """Interactive setup wizard for brainplorp."""

    click.echo("🧠 brainplorp Setup Wizard")
    click.echo("=" * 50)
    click.echo()

    config = {}

    # Step 1: Detect Obsidian vault
    click.echo("Step 1: Obsidian Vault Location")
    vault_path = detect_obsidian_vault()

    if vault_path:
        click.echo(f"  ✓ Found Obsidian vault: {vault_path}")
        use_detected = click.confirm("  Use this vault?", default=True)
        if use_detected:
            config['vault_path'] = str(vault_path)
        else:
            config['vault_path'] = click.prompt("  Enter vault path")
    else:
        click.echo("  ℹ No Obsidian vault detected")
        config['vault_path'] = click.prompt("  Enter vault path (or press Enter to skip)", default="", show_default=False)

    click.echo()

    # Step 2: TaskWarrior sync configuration
    click.echo("Step 2: TaskWarrior Sync")
    click.echo("  For multi-computer sync, TaskWarrior needs a TaskChampion server.")
    setup_sync = click.confirm("  Configure TaskWarrior sync now?", default=True)

    if setup_sync:
        click.echo()
        click.echo("  TaskChampion Server Options:")
        click.echo("    1. Self-hosted (you run the server)")
        click.echo("    2. Cloud-hosted (recommended for testing)")
        click.echo("    3. Skip for now")

        choice = click.prompt("  Choose option", type=click.IntRange(1, 3), default=2)

        if choice == 1:
            config['taskwarrior_sync'] = {
                'enabled': True,
                'server_url': click.prompt("  Enter server URL")
            }
        elif choice == 2:
            # TODO: Provide default cloud server once we have one
            click.echo("  ℹ Cloud server setup will be available in next release")
            config['taskwarrior_sync'] = {'enabled': False}
        else:
            config['taskwarrior_sync'] = {'enabled': False}

    click.echo()

    # Step 3: Default editor
    click.echo("Step 3: Default Text Editor")
    config['default_editor'] = click.prompt("  Editor for notes", default="vim")

    click.echo()

    # Step 4: Email inbox (optional)
    click.echo("Step 4: Email Inbox (Optional)")
    setup_email = click.confirm("  Configure email inbox capture?", default=False)

    if setup_email:
        config['email'] = {
            'enabled': True,
            'imap_server': 'imap.gmail.com',
            'imap_port': 993,
            'username': click.prompt("  Gmail address"),
            'password': click.prompt("  Gmail App Password", hide_input=True),
            'inbox_label': click.prompt("  Gmail label (or INBOX)", default="INBOX"),
            'fetch_limit': 20
        }
    else:
        config['email'] = {'enabled': False}

    click.echo()

    # Step 5: Save configuration
    click.echo("Step 5: Save Configuration")
    config_path = Path.home() / '.config' / 'brainplorp' / 'config.yaml'
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    click.echo(f"  ✓ Config saved to {config_path}")
    click.echo()

    # Step 6: Configure Claude Desktop MCP
    click.echo("Step 6: Claude Desktop MCP Configuration")
    setup_mcp = click.confirm("  Configure MCP for Claude Desktop?", default=True)

    if setup_mcp:
        configure_mcp()

    click.echo()
    click.echo("=" * 50)
    click.echo("✅ Setup complete!")
    click.echo()
    click.echo("Next steps:")
    click.echo("  1. Run 'brainplorp start' to create your first daily note")
    click.echo("  2. Open Claude Desktop to use MCP tools")
    click.echo("  3. See 'brainplorp --help' for all commands")
    click.echo()


def detect_obsidian_vault() -> Path | None:
    """Detect Obsidian vault in standard locations."""

    # Check iCloud Drive
    icloud_path = Path.home() / 'Library' / 'Mobile Documents' / 'iCloud~md~obsidian'
    if icloud_path.exists():
        # Find first vault folder
        for item in icloud_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                return item

    # Check local Documents
    docs_vaults = Path.home() / 'Documents' / 'Obsidian Vaults'
    if docs_vaults.exists():
        for item in docs_vaults.iterdir():
            if item.is_dir() and (item / '.obsidian').exists():
                return item

    # Check common locations
    for location in [
        Path.home() / 'vault',
        Path.home() / 'Obsidian',
        Path.home() / 'Documents' / 'vault'
    ]:
        if location.exists() and (location / '.obsidian').exists():
            return location

    return None


def configure_mcp():
    """Configure Claude Desktop MCP integration."""

    claude_config_path = Path.home() / 'Library' / 'Application Support' / 'Claude' / 'claude_desktop_config.json'

    if not claude_config_path.exists():
        click.echo("  ℹ Claude Desktop config not found")
        click.echo(f"    Expected location: {claude_config_path}")
        click.echo("    Install Claude Desktop first, then run 'brainplorp setup' again")
        return

    # Read existing config
    with open(claude_config_path, 'r') as f:
        claude_config = json.load(f)

    # Get brainplorp-mcp path
    brainplorp_mcp_path = which_command('brainplorp-mcp')

    if not brainplorp_mcp_path:
        click.echo("  ⚠ brainplorp-mcp command not found")
        return

    # Add or update brainplorp server
    if 'mcpServers' not in claude_config:
        claude_config['mcpServers'] = {}

    claude_config['mcpServers']['brainplorp'] = {
        'command': str(brainplorp_mcp_path),
        'args': [],
        'env': {}
    }

    # Backup existing config
    backup_path = claude_config_path.parent / 'claude_desktop_config.json.backup'
    if claude_config_path.exists():
        shutil.copy2(claude_config_path, backup_path)
        click.echo(f"  ℹ Backed up existing config to {backup_path}")

    # Write updated config
    with open(claude_config_path, 'w') as f:
        json.dump(claude_config, f, indent=2)

    click.echo("  ✓ Claude Desktop MCP configured")
    click.echo("    Restart Claude Desktop to load brainplorp tools")


def which_command(cmd: str) -> Path | None:
    """Find command in PATH."""
    result = shutil.which(cmd)
    return Path(result) if result else None


@click.command()
def configure_mcp_standalone():
    """
    Configure Claude Desktop MCP integration.

    Run this command to add brainplorp to Claude Desktop's MCP servers.
    Can be run multiple times safely - will update existing configuration.
    """
    click.echo("🧠 Configuring Claude Desktop MCP")
    click.echo("=" * 50)
    click.echo()

    configure_mcp()

    click.echo()
    click.echo("Next steps:")
    click.echo("  1. Restart Claude Desktop")
    click.echo("  2. Look for brainplorp tools in Claude Desktop")
    click.echo("  3. Try: 'Start my day' or 'What tasks do I have?'")
    click.echo()
