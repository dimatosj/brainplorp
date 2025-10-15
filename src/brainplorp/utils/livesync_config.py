"""
LiveSync Configuration Utilities

Handles Obsidian Self-hosted LiveSync plugin configuration for vault sync.
"""

import json
import re
import secrets
from pathlib import Path
from typing import Dict, Optional, Tuple

# Plugin identifiers
LIVESYNC_PLUGIN_ID = "obsidian-livesync"
LIVESYNC_PLUGIN_NAME = "Self-hosted LiveSync"


def sanitize_username(username: str) -> str:
    """
    Convert OS username to valid CouchDB database name.

    CouchDB requirements:
    - Lowercase only
    - Alphanumeric + hyphen + underscore
    - Must start with letter

    Args:
        username: OS username (may contain spaces, uppercase, special chars)

    Returns:
        Sanitized username safe for CouchDB

    Examples:
        >>> sanitize_username("John Smith")
        'john-smith'
        >>> sanitize_username("jsd123")
        'jsd123'
        >>> sanitize_username("123user")
        'user-123user'
    """
    # Lowercase
    username = username.lower()

    # Replace spaces with hyphens
    username = username.replace(' ', '-')

    # Remove invalid characters (keep alphanumeric, hyphen, underscore)
    username = re.sub(r'[^a-z0-9\-_]', '', username)

    # Ensure starts with letter (CouchDB requirement)
    if not username or not username[0].isalpha():
        username = 'user-' + username

    return username


def generate_credentials(username: str) -> Tuple[str, str, str]:
    """
    Generate CouchDB credentials for user.

    Args:
        username: OS username

    Returns:
        Tuple of (sanitized_username, database_name, password)
    """
    sanitized = sanitize_username(username)
    database = f"user-{sanitized}-vault"
    password = secrets.token_urlsafe(32)

    return (sanitized, database, password)


def check_livesync_installed(vault_path: Path) -> bool:
    """
    Check if LiveSync plugin is installed in Obsidian vault.

    Args:
        vault_path: Path to Obsidian vault

    Returns:
        True if plugin is installed
    """
    plugin_dir = vault_path / ".obsidian" / "plugins" / LIVESYNC_PLUGIN_ID
    return plugin_dir.exists() and (plugin_dir / "manifest.json").exists()


def check_livesync_configured(vault_path: Path) -> Optional[str]:
    """
    Check if LiveSync plugin is already configured.

    Args:
        vault_path: Path to Obsidian vault

    Returns:
        Existing server URL if configured, None otherwise
    """
    config_file = vault_path / ".obsidian" / "plugins" / LIVESYNC_PLUGIN_ID / "data.json"

    if not config_file.exists():
        return None

    try:
        config = json.loads(config_file.read_text())
        return config.get('couchDB_URI')
    except (json.JSONDecodeError, OSError):
        return None


def generate_livesync_config(
    server_url: str,
    database: str,
    username: str,
    password: str
) -> Dict:
    """
    Generate LiveSync plugin configuration.

    Args:
        server_url: CouchDB server URL (e.g., https://couch-brainplorp-sync.fly.dev)
        database: CouchDB database name (e.g., user-jsd-vault)
        username: CouchDB username
        password: CouchDB password

    Returns:
        Configuration dict ready to write to data.json
    """
    return {
        "couchDB_URI": server_url,
        "couchDB_USER": username,
        "couchDB_PASSWORD": password,
        "couchDB_DBNAME": database,
        "liveSync": True,
        "syncOnSave": True,
        "syncOnStart": True,
        "conflictResolutionStrategy": "automatic",
        "batchSize": 50,
        "batchSizeLimit": 100,
        "useTimeouts": True
    }


def write_livesync_config(vault_path: Path, config: Dict) -> None:
    """
    Write LiveSync plugin configuration to vault.

    Merges provided config into existing config to preserve plugin settings.

    Args:
        vault_path: Path to Obsidian vault
        config: Configuration dict from generate_livesync_config()

    Raises:
        FileNotFoundError: If plugin is not installed
        OSError: If config cannot be written
    """
    plugin_dir = vault_path / ".obsidian" / "plugins" / LIVESYNC_PLUGIN_ID

    if not plugin_dir.exists():
        raise FileNotFoundError(f"LiveSync plugin not installed at {plugin_dir}")

    config_file = plugin_dir / "data.json"

    # Read existing config if it exists
    existing_config = {}
    if config_file.exists():
        try:
            existing_config = json.loads(config_file.read_text())
        except (json.JSONDecodeError, OSError):
            # If config is corrupted, start fresh
            existing_config = {}

    # Merge new config into existing (new values override)
    existing_config.update(config)

    config_file.write_text(json.dumps(existing_config, indent=2))


def get_plugin_path(vault_path: Path) -> Path:
    """
    Get LiveSync plugin directory path.

    Args:
        vault_path: Path to Obsidian vault

    Returns:
        Path to plugin directory
    """
    return vault_path / ".obsidian" / "plugins" / LIVESYNC_PLUGIN_ID
