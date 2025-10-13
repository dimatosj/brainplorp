"""
Diagnostic check functions for brainplorp system health.

These functions are used by both the doctor command and setup wizard
to validate system configuration.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, Any

import yaml


def check_taskwarrior(verbose: bool = False) -> Dict[str, Any]:
    """
    Check if TaskWarrior is installed and functional.

    Tests:
    1. TaskWarrior binary exists in PATH
    2. Version check completes (doesn't hang)
    3. Basic operations work (task count)

    Args:
        verbose: If True, include detailed diagnostic information

    Returns:
        Dictionary with keys:
        - passed: bool
        - message: str (user-friendly status message)
        - fix: str (optional, how to fix the issue)
        - details: dict (optional, additional diagnostic info)
    """
    try:
        # Test 1: Check if 'task' command exists
        which_result = subprocess.run(
            ['which', 'task'],
            capture_output=True,
            text=True,
            timeout=2
        )

        if which_result.returncode != 0:
            return {
                'passed': False,
                'message': 'TaskWarrior not found in PATH',
                'fix': 'Install TaskWarrior: brew install dimatosj/brainplorp/taskwarrior-pinned'
            }

        task_path = which_result.stdout.strip()

        # Test 2: Check version (with timeout to catch hangs)
        try:
            version_result = subprocess.run(
                ['task', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
        except subprocess.TimeoutExpired:
            return {
                'passed': False,
                'message': 'TaskWarrior hangs on --version (known issue with 3.4.1)',
                'fix': 'Downgrade TaskWarrior: brew uninstall task && brew install dimatosj/brainplorp/taskwarrior-pinned',
                'details': {
                    'path': task_path,
                    'issue': 'TaskWarrior 3.4.1 has a first-run initialization bug'
                }
            }

        if version_result.returncode != 0:
            return {
                'passed': False,
                'message': f'TaskWarrior failed to run: {version_result.stderr[:100]}',
                'fix': 'Reinstall TaskWarrior: brew reinstall dimatosj/brainplorp/taskwarrior-pinned'
            }

        version = version_result.stdout.strip()

        # Check for problematic version
        if '3.4.1' in version:
            return {
                'passed': False,
                'message': f'TaskWarrior {version} has known hang issues',
                'fix': 'Downgrade: brew uninstall task && brew install dimatosj/brainplorp/taskwarrior-pinned',
                'details': {
                    'path': task_path,
                    'version': version,
                    'issue': 'Version 3.4.1 hangs on first initialization'
                }
            }

        # Test 3: Try basic operation (with timeout)
        try:
            count_result = subprocess.run(
                ['task', 'count'],
                capture_output=True,
                text=True,
                timeout=5
            )
        except subprocess.TimeoutExpired:
            return {
                'passed': False,
                'message': f'TaskWarrior {version} hangs on operations',
                'fix': 'Try: rm -rf ~/.task ~/.taskrc && task add "init"'
            }

        if count_result.returncode != 0:
            return {
                'passed': False,
                'message': f'TaskWarrior {version} installed but not functional',
                'fix': 'Initialize: rm -rf ~/.task ~/.taskrc && task add "init task" && task 1 done',
                'details': {
                    'error': count_result.stderr[:200]
                }
            }

        task_count = count_result.stdout.strip()

        return {
            'passed': True,
            'message': f'{version} working ({task_count} tasks)',
            'details': {
                'path': task_path,
                'version': version,
                'task_count': task_count
            }
        }

    except Exception as e:
        return {
            'passed': False,
            'message': f'TaskWarrior check failed: {str(e)}',
            'fix': 'Check TaskWarrior installation: brew list task'
        }


def check_python_dependencies(verbose: bool = False) -> Dict[str, Any]:
    """Check if required Python packages are installed."""
    required = {
        'click': 'Click',
        'yaml': 'PyYAML',
        'rich': 'Rich'
    }

    missing = []
    installed = []

    for module, package in required.items():
        try:
            __import__(module)
            installed.append(package)
        except ImportError:
            missing.append(package)

    if missing:
        return {
            'passed': False,
            'message': f'Missing dependencies: {", ".join(missing)}',
            'fix': 'Reinstall brainplorp: brew reinstall brainplorp',
            'details': {
                'missing': missing,
                'installed': installed
            }
        }

    return {
        'passed': True,
        'message': f'All dependencies installed ({len(installed)} packages)',
        'details': {'installed': installed}
    }


def check_config_validity(verbose: bool = False) -> Dict[str, Any]:
    """Check if config file exists and is valid YAML."""
    config_path = Path.home() / '.config' / 'brainplorp' / 'config.yaml'

    if not config_path.exists():
        return {
            'passed': False,
            'message': 'Config file not found',
            'fix': 'Run: brainplorp setup',
            'details': {'expected_path': str(config_path)}
        }

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Check required fields
        required_fields = ['vault_path']
        missing_fields = [f for f in required_fields if f not in config]

        if missing_fields:
            return {
                'passed': False,
                'message': f'Config missing fields: {", ".join(missing_fields)}',
                'fix': 'Re-run: brainplorp setup',
                'details': {
                    'path': str(config_path),
                    'missing_fields': missing_fields
                }
            }

        return {
            'passed': True,
            'message': f'Config valid at {config_path.name}',
            'details': {
                'path': str(config_path),
                'vault_path': config.get('vault_path')
            }
        }

    except yaml.YAMLError as e:
        return {
            'passed': False,
            'message': f'Config file invalid YAML: {str(e)[:50]}',
            'fix': 'Fix config or re-run: brainplorp setup',
            'details': {
                'path': str(config_path),
                'error': str(e)
            }
        }
    except Exception as e:
        return {
            'passed': False,
            'message': f'Config check failed: {str(e)}',
            'fix': 'Re-run: brainplorp setup'
        }


def check_vault_access(verbose: bool = False) -> Dict[str, Any]:
    """Check if Obsidian vault is accessible."""
    config_path = Path.home() / '.config' / 'brainplorp' / 'config.yaml'

    if not config_path.exists():
        return {
            'passed': False,
            'message': 'Config file not found (run brainplorp setup first)',
            'fix': 'Run: brainplorp setup'
        }

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except Exception:
        return {
            'passed': False,
            'message': 'Cannot read config file',
            'fix': 'Re-run: brainplorp setup'
        }

    vault_path = Path(config.get('vault_path', ''))

    if not vault_path:
        return {
            'passed': False,
            'message': 'Vault path not configured',
            'fix': 'Run: brainplorp setup'
        }

    if not vault_path.exists():
        return {
            'passed': False,
            'message': f'Vault not found: {vault_path}',
            'fix': 'Update vault path: brainplorp setup',
            'details': {'vault_path': str(vault_path)}
        }

    if not vault_path.is_dir():
        return {
            'passed': False,
            'message': f'Vault path is not a directory: {vault_path}',
            'fix': 'Update vault path: brainplorp setup'
        }

    # Check for typical Obsidian vault structure
    has_obsidian_dir = (vault_path / '.obsidian').exists()

    return {
        'passed': True,
        'message': f'Vault accessible at {vault_path.name}/',
        'details': {
            'vault_path': str(vault_path),
            'has_obsidian_config': has_obsidian_dir
        }
    }


def check_mcp_configuration(verbose: bool = False) -> Dict[str, Any]:
    """Check if MCP server is configured for Claude Desktop."""
    claude_config_path = (
        Path.home() / 'Library' / 'Application Support' / 'Claude' / 'claude_desktop_config.json'
    )

    if not claude_config_path.exists():
        return {
            'passed': False,
            'message': 'Claude Desktop config not found',
            'fix': 'Run: brainplorp mcp (requires Claude Desktop installed)',
            'details': {'expected_path': str(claude_config_path)}
        }

    try:
        with open(claude_config_path) as f:
            config = json.load(f)

        if 'mcpServers' not in config:
            return {
                'passed': False,
                'message': 'MCP servers section missing',
                'fix': 'Run: brainplorp mcp'
            }

        if 'brainplorp' not in config['mcpServers']:
            return {
                'passed': False,
                'message': 'brainplorp MCP server not configured',
                'fix': 'Run: brainplorp mcp',
                'details': {
                    'configured_servers': list(config['mcpServers'].keys())
                }
            }

        brainplorp_config = config['mcpServers']['brainplorp']

        return {
            'passed': True,
            'message': 'MCP server configured for Claude Desktop',
            'details': {
                'command': brainplorp_config.get('command'),
                'config_path': str(claude_config_path)
            }
        }

    except json.JSONDecodeError as e:
        return {
            'passed': False,
            'message': f'Claude Desktop config invalid JSON: {str(e)[:50]}',
            'fix': 'Fix Claude config or run: brainplorp mcp'
        }
    except Exception as e:
        return {
            'passed': False,
            'message': f'MCP config check failed: {str(e)}',
            'fix': 'Run: brainplorp mcp'
        }
