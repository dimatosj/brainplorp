# ABOUTME: Configuration management for plorp - loads user settings from YAML config file
# ABOUTME: Handles default config creation, loading, saving, and merging with defaults
"""
Configuration management for plorp.

Loads configuration from YAML file, creates defaults if not found.
Config location: ~/.config/plorp/config.yaml (or $XDG_CONFIG_HOME/plorp/config.yaml)
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any
import yaml


# Default configuration values
DEFAULT_CONFIG: Dict[str, Any] = {
    "vault_path": os.path.expanduser("~/vault"),
    "taskwarrior_data": os.path.expanduser("~/.task"),
    "inbox_email": None,
    "default_editor": os.environ.get("EDITOR", "vim"),
}


def get_config_path() -> Path:
    """
    Get the path to the configuration file.

    Returns:
        Path to config file (e.g., ~/.config/plorp/config.yaml)

    Priority:
        1. $XDG_CONFIG_HOME/plorp/config.yaml
        2. ~/.config/plorp/config.yaml
    """
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "plorp" / "config.yaml"

    return Path.home() / ".config" / "plorp" / "config.yaml"


def load_config() -> Dict[str, Any]:
    """
    Load configuration from file or create default.

    If config file doesn't exist, creates it with default values.
    Validates vault_path and creates it if needed.

    Returns:
        Configuration dictionary with all settings.

    Example:
        >>> config = load_config()
        >>> vault_path = config['vault_path']
    """
    config_path = get_config_path()

    if not config_path.exists():
        # Create default config
        save_config(DEFAULT_CONFIG)
        config = DEFAULT_CONFIG.copy()
    else:
        with open(config_path) as f:
            user_config = yaml.safe_load(f)

        # Validate that we got a dict
        if not isinstance(user_config, dict):
            user_config = {}

        # Merge with defaults (user config overrides defaults)
        config = DEFAULT_CONFIG.copy()
        config.update(user_config)

    # Validate and create vault_path
    vault_path = Path(config["vault_path"])

    if vault_path.exists():
        if not vault_path.is_dir():
            print(
                f"⚠️  Warning: vault_path is not a directory: {vault_path}",
                file=sys.stderr,
            )
    else:
        # Create vault directory
        vault_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created vault directory: {vault_path}")

    return config


def save_config(config: Dict[str, Any]) -> None:
    """
    Save configuration to file.

    Args:
        config: Configuration dictionary to save

    Example:
        >>> config = load_config()
        >>> config['vault_path'] = '/custom/path'
        >>> save_config(config)
    """
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
