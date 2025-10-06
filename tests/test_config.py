# ABOUTME: Tests for configuration management - validates loading, saving, and defaults
# ABOUTME: Uses temporary directories to test config file creation without affecting system
"""Tests for configuration management."""
import pytest
from pathlib import Path
from plorp.config import get_config_path, load_config, save_config, DEFAULT_CONFIG


def test_default_config_structure():
    """Test that DEFAULT_CONFIG has required fields."""
    assert "vault_path" in DEFAULT_CONFIG
    assert "taskwarrior_data" in DEFAULT_CONFIG
    assert "inbox_email" in DEFAULT_CONFIG
    assert "default_editor" in DEFAULT_CONFIG


def test_get_config_path_with_xdg(monkeypatch):
    """Test config path uses XDG_CONFIG_HOME if set."""
    monkeypatch.setenv("XDG_CONFIG_HOME", "/custom/config")

    path = get_config_path()

    assert path == Path("/custom/config/plorp/config.yaml")


def test_get_config_path_default(monkeypatch):
    """Test config path falls back to ~/.config if XDG not set."""
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    path = get_config_path()

    assert path == Path.home() / ".config" / "plorp" / "config.yaml"


def test_load_config_creates_default(tmp_path, monkeypatch, capsys):
    """Test that load_config creates default config if none exists."""
    config_dir = tmp_path / "plorp"
    config_file = config_dir / "config.yaml"

    # Create a custom vault path in tmp_path
    vault_dir = tmp_path / "test_vault"

    # Mock both get_config_path and DEFAULT_CONFIG
    monkeypatch.setattr("plorp.config.get_config_path", lambda: config_file)
    monkeypatch.setattr(
        "plorp.config.DEFAULT_CONFIG",
        {
            "vault_path": str(vault_dir),
            "taskwarrior_data": "~/.task",
            "inbox_email": None,
            "default_editor": "vim",
        },
    )

    config = load_config()

    assert config_file.exists()
    assert config["vault_path"] == str(vault_dir)

    # Check vault was created
    assert vault_dir.exists()
    assert vault_dir.is_dir()

    # Check creation message printed
    captured = capsys.readouterr()
    assert "Created vault directory" in captured.out


def test_load_config_existing(tmp_path, monkeypatch):
    """Test loading existing config file."""
    config_dir = tmp_path / "plorp"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"

    # Create vault directory first
    vault_dir = tmp_path / "custom_vault"
    vault_dir.mkdir()

    # Write custom config
    custom_config = {"vault_path": str(vault_dir), "taskwarrior_data": "/custom/task"}

    import yaml

    with open(config_file, "w") as f:
        yaml.dump(custom_config, f)

    monkeypatch.setattr("plorp.config.get_config_path", lambda: config_file)

    config = load_config()

    assert config["vault_path"] == str(vault_dir)
    assert config["taskwarrior_data"] == "/custom/task"
    # Should merge with defaults
    assert "default_editor" in config


def test_load_config_creates_vault_if_not_exists(tmp_path, monkeypatch, capsys):
    """Test that load_config creates vault directory if it doesn't exist."""
    config_dir = tmp_path / "plorp"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"

    vault_dir = tmp_path / "nonexistent_vault"

    # Write config with nonexistent vault path
    custom_config = {"vault_path": str(vault_dir)}

    import yaml

    with open(config_file, "w") as f:
        yaml.dump(custom_config, f)

    monkeypatch.setattr("plorp.config.get_config_path", lambda: config_file)

    config = load_config()

    # Vault should be created
    assert vault_dir.exists()
    assert vault_dir.is_dir()

    captured = capsys.readouterr()
    assert "Created vault directory" in captured.out


def test_load_config_warns_if_vault_is_file(tmp_path, monkeypatch, capsys):
    """Test that load_config warns if vault_path is a file."""
    config_dir = tmp_path / "plorp"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"

    # Create a file instead of directory
    vault_file = tmp_path / "vault_file"
    vault_file.write_text("I'm a file, not a directory")

    custom_config = {"vault_path": str(vault_file)}

    import yaml

    with open(config_file, "w") as f:
        yaml.dump(custom_config, f)

    monkeypatch.setattr("plorp.config.get_config_path", lambda: config_file)

    config = load_config()

    # Should still return config
    assert config["vault_path"] == str(vault_file)

    # Should warn to stderr
    captured = capsys.readouterr()
    assert "Warning" in captured.err or "warning" in captured.err.lower()
    assert "not a directory" in captured.err.lower()


def test_save_config(tmp_path, monkeypatch):
    """Test saving configuration."""
    config_dir = tmp_path / "plorp"
    config_file = config_dir / "config.yaml"

    monkeypatch.setattr("plorp.config.get_config_path", lambda: config_file)

    test_config = {"vault_path": "/test/vault"}
    save_config(test_config)

    assert config_file.exists()

    # Verify saved content
    import yaml

    with open(config_file) as f:
        saved = yaml.safe_load(f)

    assert saved["vault_path"] == "/test/vault"


def test_load_config_handles_invalid_yaml(tmp_path, monkeypatch):
    """Test load_config handles non-dict YAML (like lists or strings)."""
    config_dir = tmp_path / "plorp"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"

    # Write YAML that's a list, not a dict
    with open(config_file, "w") as f:
        f.write("- item1\n- item2\n")

    monkeypatch.setattr("plorp.config.get_config_path", lambda: config_file)

    config = load_config()

    # Should fall back to defaults
    assert config == DEFAULT_CONFIG
