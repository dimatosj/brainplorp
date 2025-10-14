# ABOUTME: Interactive setup wizard for brainplorp first-time configuration
# ABOUTME: Detects Obsidian vault, configures TaskWarrior sync, email, and Claude Desktop MCP

import click
import os
import sys
from pathlib import Path
import json
import yaml
import shutil
import keyring
import uuid
import secrets
import subprocess

from brainplorp.utils.diagnostics import check_taskwarrior
from brainplorp.utils.livesync_config import (
    check_livesync_installed,
    check_livesync_configured,
    generate_credentials,
    generate_livesync_config,
    write_livesync_config,
    LIVESYNC_PLUGIN_NAME
)
from brainplorp.integrations.couchdb import CouchDBClient, CouchDBError, CouchDBAuthError


def generate_sync_credentials() -> dict:
    """Generate TaskChampion sync credentials."""
    return {
        'client_id': str(uuid.uuid4()),
        'encryption_secret': secrets.token_hex(32)
    }


def configure_taskwarrior_sync(server_url: str, client_id: str, secret: str) -> bool:
    """
    Configure TaskWarrior sync settings.
    Returns True if successful, False if error.
    """
    try:
        # Use rc.confirmation=off to avoid interactive prompts
        subprocess.run(['task', 'rc.confirmation=off', 'config', 'sync.server.url', server_url],
                      check=True, capture_output=True, timeout=10)
        subprocess.run(['task', 'rc.confirmation=off', 'config', 'sync.server.client_id', client_id],
                      check=True, capture_output=True, timeout=10)
        subprocess.run(['task', 'rc.confirmation=off', 'config', 'sync.encryption_secret', secret],
                      check=True, capture_output=True, timeout=10)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


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

    # Step 1.5: TaskWarrior Validation (NEW - Sprint 10.1.1)
    click.echo("Step 1.5: Checking TaskWarrior...")

    tw_check = check_taskwarrior(verbose=False)

    if not tw_check['passed']:
        click.echo()
        click.secho(f"  ✗ TaskWarrior issue detected:", fg='red', bold=True)
        click.echo(f"     {tw_check['message']}")
        click.echo()
        click.secho(f"  Fix:", fg='yellow', bold=True)
        click.echo(f"     {tw_check['fix']}")
        click.echo()

        # Check if it's the known 3.4.1 issue
        if '3.4.1' in tw_check.get('message', ''):
            click.secho("  ⚠ Known Issue: TaskWarrior 3.4.1 hang bug", fg='yellow', bold=True)
            click.echo("     This is an upstream TaskWarrior bug, not a brainplorp issue.")
            click.echo("     See: https://github.com/dimatosj/brainplorp#known-issues")

        click.echo()
        click.secho("  Setup cannot continue until TaskWarrior is working.", fg='red')
        click.echo("  Run 'brainplorp setup' again after fixing TaskWarrior.")
        click.echo()
        sys.exit(1)
    else:
        click.echo(f"  ✓ {tw_check['message']}")

    click.echo()

    # Step 2: TaskWarrior Cloud Sync
    click.echo("Step 2: TaskWarrior Sync")
    click.echo("  Configuring brainplorp Cloud Sync...")
    click.echo()

    # Check if already configured
    try:
        existing = subprocess.run(['task', 'config', 'sync.server.url'],
                                 capture_output=True, text=True, timeout=5)
        if existing.stdout.strip():
            click.echo(f"  ⚠ TaskWarrior sync already configured: {existing.stdout.strip()}")
            overwrite = click.confirm("  Overwrite with brainplorp cloud sync?", default=False)
            if not overwrite:
                click.echo("  Keeping existing sync configuration.")
                config['taskwarrior_sync'] = {'enabled': True, 'type': 'existing'}
                click.echo()
                # Continue to next step
            else:
                # User wants to overwrite, continue with cloud sync setup
                pass
        else:
            # No existing sync config, proceed
            pass
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        # TaskWarrior not responding or error, proceed anyway
        pass

    # Only proceed with sync setup if we haven't kept existing config
    if config.get('taskwarrior_sync', {}).get('type') != 'existing':
        # Ask: new or existing credentials
        use_existing = click.confirm("  Do you have sync credentials from another computer?",
                                     default=False)

        server_url = "https://brainplorp-sync.fly.dev"

        if use_existing:
            # Enter existing credentials
            click.echo()
            click.echo("  Enter credentials from your other computer:")
            client_id = click.prompt("  Client ID")
            encryption_secret = click.prompt("  Encryption Secret", hide_input=True)
        else:
            # Generate new credentials
            click.echo()
            click.echo("  Generating new sync credentials...")
            creds = generate_sync_credentials()
            client_id = creds['client_id']
            encryption_secret = creds['encryption_secret']

        # Configure TaskWarrior
        click.echo()
        click.echo("  Configuring TaskWarrior...")
        success = configure_taskwarrior_sync(server_url, client_id, encryption_secret)

        if not success:
            click.echo("  ✗ Failed to configure TaskWarrior")
            config['taskwarrior_sync'] = {'enabled': False}
        else:
            # Save to brainplorp config
            config['taskwarrior_sync'] = {
                'enabled': True,
                'type': 'cloud',
                'server_url': server_url,
                'client_id': client_id,
                'encryption_secret': encryption_secret
            }

            # Test connection and perform first sync
            click.echo()
            click.echo("  Testing connection...")

            try:
                sync_result = subprocess.run(['task', 'sync'],
                                             capture_output=True,
                                             text=True,
                                             timeout=30)

                if sync_result.returncode == 0:
                    # Successful sync - check task count
                    try:
                        task_count_result = subprocess.run(['task', 'count'],
                                                          capture_output=True,
                                                          text=True,
                                                          timeout=5)
                        task_count = int(task_count_result.stdout.strip()) if task_count_result.returncode == 0 else 0
                    except (ValueError, subprocess.TimeoutExpired):
                        task_count = 0

                    if use_existing and task_count > 0:
                        # Computer 2+ downloading existing tasks
                        click.echo(f"  ✓ Sync successful! Downloaded {task_count} tasks from server.")
                        click.echo()
                        click.secho("  🎉 Your tasks are now available on this computer!",
                                   fg='green', bold=True)
                        click.echo(f"     Run 'task list' to see your {task_count} tasks.")
                    elif not use_existing and task_count > 0:
                        # Computer 1 uploading existing tasks
                        click.echo(f"  ✓ Sync successful! Uploaded {task_count} tasks to server.")
                        click.echo()
                        click.echo("  Your tasks are now synced to the cloud.")
                    else:
                        # Fresh start on both sides
                        click.echo("  ✓ Sync successful!")
                else:
                    # Sync failed
                    click.echo("  ⚠ Couldn't reach server, but config saved.")
                    click.echo("    Try 'task sync' later to verify.")
                    if use_existing:
                        click.echo()
                        click.secho("  💡 First sync will download your tasks from the server.",
                                   fg='cyan')
                        click.echo("     Your tasks from Computer 1 will appear after first successful sync.")

            except subprocess.TimeoutExpired:
                click.echo("  ⚠ Sync timed out, but config saved.")
                click.echo("    Try 'task sync' later to verify.")

            # Display credentials (for Computer 2 setup)
            if not use_existing:
                click.echo()
                click.secho("  📋 IMPORTANT: Save these credentials for your other computers:",
                           fg='yellow', bold=True)
                click.echo(f"     Client ID: {client_id}")
                click.echo(f"     Secret: {encryption_secret}")
                click.echo()
                click.echo("  On your other Mac:")
                click.echo("    1. Install brainplorp: brew install dimatosj/brainplorp/brainplorp")
                click.echo("    2. Run: brainplorp setup")
                click.echo("    3. Answer 'Yes' when asked about existing credentials")
                click.echo("    4. Enter the credentials above")
                click.echo("    5. First sync will download all your tasks automatically")
                click.echo()
                click.echo("  (Credentials also saved to: ~/.config/brainplorp/config.yaml)")
            else:
                # Computer 2+ just finished first sync
                if 'sync_result' in locals() and sync_result.returncode == 0 and task_count > 0:
                    click.echo()
                    click.echo("  Next steps:")
                    click.echo("    • Run 'brainplorp start' to generate today's daily note")
                    click.echo("    • Add/complete tasks on either computer")
                    click.echo("    • Run 'task sync' periodically to keep computers in sync")

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

    # Step 5: Vault Sync (Optional - Sprint 10.3)
    click.echo("Step 5: Vault Sync (Optional)")
    click.echo("  Sync your vault across devices (Mac, iPhone, iPad, etc.)")
    setup_vault_sync = click.confirm("  Configure vault sync?", default=False)

    if setup_vault_sync:
        vault_sync_config = configure_vault_sync(config.get('vault_path'))
        if vault_sync_config:
            config['vault_sync'] = vault_sync_config
    else:
        config['vault_sync'] = {'enabled': False}

    click.echo()

    # Step 6: Save configuration
    click.echo("Step 6: Save Configuration")
    config_path = Path.home() / '.config' / 'brainplorp' / 'config.yaml'
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    click.echo(f"  ✓ Config saved to {config_path}")
    click.echo()

    # Step 7: Configure Claude Desktop MCP
    click.echo("Step 7: Claude Desktop MCP Configuration")
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


def configure_vault_sync(vault_path_str: str | None) -> dict | None:
    """
    Configure vault sync via CouchDB + Obsidian LiveSync.

    Args:
        vault_path_str: Path to Obsidian vault

    Returns:
        Vault sync configuration dict, or None if setup failed/skipped
    """
    # Constants
    COUCHDB_SERVER_URL = "https://couch-brainplorp-sync.fly.dev"
    COUCHDB_ADMIN_USER = "admin"
    COUCHDB_ADMIN_PASSWORD = "CZzAQ7wnpPHY-tL0dYu20VY9-vcQHWdvENs0rLkye_0"

    # Validate vault path
    if not vault_path_str:
        click.echo("  ⚠ Vault path not configured. Please configure vault first.")
        return None

    vault_path = Path(vault_path_str)

    if not vault_path.exists():
        click.echo(f"  ⚠ Vault path does not exist: {vault_path}")
        return None

    # Check if LiveSync plugin is installed
    if not check_livesync_installed(vault_path):
        click.echo(f"  ⚠ {LIVESYNC_PLUGIN_NAME} plugin not installed")
        click.echo()
        click.echo("  To install:")
        click.echo("    1. Open Obsidian")
        click.echo("    2. Settings → Community Plugins → Browse")
        click.echo(f"    3. Search '{LIVESYNC_PLUGIN_NAME}'")
        click.echo("    4. Click Install, then Enable")
        click.echo("    5. Run 'brainplorp setup' again")
        click.echo()
        return None

    # Check if LiveSync is already configured
    existing_server = check_livesync_configured(vault_path)
    if existing_server:
        click.echo(f"  ⚠ LiveSync already configured")
        click.echo(f"     Current server: {existing_server}")
        click.echo()
        click.echo("  To reconfigure:")
        click.echo("    1. Open Obsidian → Settings → Self-hosted LiveSync")
        click.echo("    2. Disable sync")
        click.echo("    3. Run 'brainplorp setup' again")
        click.echo()
        return None

    click.echo(f"  ✓ {LIVESYNC_PLUGIN_NAME} plugin installed")
    click.echo()

    # Ask if user has credentials from another computer
    has_credentials = click.confirm("  Do you have CouchDB credentials from another computer?", default=False)

    if has_credentials:
        # Flow 2: Additional computer - use existing credentials
        click.echo()
        click.echo("  Enter credentials from your other computer:")
        username = click.prompt("  Username")
        database = click.prompt("  Database")
        password = click.prompt("  Password", hide_input=True)

    else:
        # Flow 1: First computer - generate new credentials
        click.echo()
        click.echo("  Generating CouchDB credentials...")

        username, database, password = generate_credentials(os.getlogin())

        # Create database and user in CouchDB
        try:
            client = CouchDBClient(COUCHDB_SERVER_URL, COUCHDB_ADMIN_USER, COUCHDB_ADMIN_PASSWORD)

            click.echo("  Connecting to CouchDB server...")
            client.test_connection()

            click.echo(f"  Creating database: {database}")
            client.setup_vault_database(database, username, password)

            click.echo("  ✓ CouchDB configured")

        except CouchDBAuthError as e:
            click.echo(f"  ✗ Authentication failed: {e}")
            return None

        except CouchDBError as e:
            click.echo(f"  ✗ CouchDB error: {e}")
            return None

    # Write LiveSync configuration
    try:
        config = generate_livesync_config(COUCHDB_SERVER_URL, database, username, password)
        write_livesync_config(vault_path, config)
        click.echo("  ✓ LiveSync plugin configured")

    except Exception as e:
        click.echo(f"  ✗ Failed to write LiveSync config: {e}")
        return None

    # Store credentials in OS keychain
    try:
        keyring.set_password("brainplorp-vault-sync", username, password)
        click.echo("  ✓ Credentials stored in OS keychain")

    except Exception as e:
        click.echo(f"  ⚠ Failed to store password in keychain: {e}")
        # Non-fatal - config still works

    # Display credentials for user to save
    click.echo()
    click.echo("  " + "=" * 60)
    click.echo("  📋 SAVE THESE CREDENTIALS FOR YOUR OTHER COMPUTERS:")
    click.echo("  " + "=" * 60)
    click.echo(f"  Server:   {COUCHDB_SERVER_URL}")
    click.echo(f"  Database: {database}")
    click.echo(f"  Username: {username}")
    click.echo(f"  Password: {password}")
    click.echo("  " + "=" * 60)
    click.echo()

    # Instructions for user
    click.echo("  📋 To complete setup:")
    click.echo("    1. Open Obsidian")
    click.echo("    2. Go to Settings → Community Plugins")
    click.echo(f"    3. Enable '{LIVESYNC_PLUGIN_NAME}'")
    click.echo("    4. Plugin will start syncing automatically")
    click.echo()
    click.echo("  🎉 Your vault will now sync across all devices!")
    click.echo()

    # Return configuration
    return {
        'enabled': True,
        'server': COUCHDB_SERVER_URL,
        'database': database,
        'username': username,
        'password_keyring': True  # Flag that password is in keyring
    }


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
