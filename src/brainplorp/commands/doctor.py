"""
brainplorp doctor command - System diagnostics and health checks.

Usage:
    brainplorp doctor
    brainplorp doctor --verbose

Checks:
- TaskWarrior installation and functionality
- Python dependencies
- Obsidian vault accessibility
- Config file validity
- MCP server configuration
"""

import sys

import click

from brainplorp.utils.diagnostics import (
    check_taskwarrior,
    check_python_dependencies,
    check_config_validity,
    check_vault_access,
    check_mcp_configuration
)


@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed diagnostic information')
def doctor(verbose: bool):
    """
    Diagnose brainplorp installation and configuration issues.

    Runs comprehensive health checks and provides actionable fix instructions.
    """
    click.echo()
    click.secho("brainplorp System Diagnostics", fg='cyan', bold=True)
    click.echo("=" * 60)
    click.echo()

    checks = [
        ('TaskWarrior', check_taskwarrior, True),   # Critical
        ('Python Dependencies', check_python_dependencies, True),
        ('Configuration File', check_config_validity, True),
        ('Obsidian Vault', check_vault_access, False),  # Not critical
        ('MCP Server', check_mcp_configuration, False)
    ]

    results = {}
    critical_failures = []

    for name, check_func, is_critical in checks:
        click.echo(f"Checking {name}...", nl=False)
        result = check_func(verbose)
        results[name] = result

        if result['passed']:
            click.secho(f" ✓", fg='green', nl=False)
            click.echo(f" {result['message']}")
            if verbose and 'details' in result:
                click.echo(f"  Details: {result['details']}")
        else:
            click.secho(f" ✗", fg='red', nl=False)
            click.echo(f" {result['message']}")
            if verbose and 'details' in result:
                click.echo(f"  Details: {result['details']}")
            if is_critical:
                critical_failures.append((name, result))

    # Summary
    click.echo()
    click.echo("=" * 60)

    if all(r['passed'] for r in results.values()):
        click.secho("✓ All checks passed!", fg='green', bold=True)
        click.echo("brainplorp is ready to use.")
        return 0

    elif not critical_failures:
        click.secho("⚠ Some non-critical checks failed", fg='yellow', bold=True)
        click.echo("brainplorp should still work, but some features may be limited.")

        click.echo()
        click.echo("Recommendations:")
        for name, result in results.items():
            if not result['passed'] and result.get('fix'):
                click.echo(f"  • {name}: {result['fix']}")
        return 0

    else:
        click.secho("✗ Critical checks failed", fg='red', bold=True)
        click.echo("brainplorp cannot function until these issues are resolved.")

        click.echo()
        click.echo("Required fixes:")
        for name, result in critical_failures:
            click.echo()
            click.secho(f"  {name}:", fg='yellow', bold=True)
            click.echo(f"    Issue: {result['message']}")
            if result.get('fix'):
                click.echo(f"    Fix: {result['fix']}")

        click.echo()
        click.echo("After fixing, run 'brainplorp doctor' again to verify.")
        return 1
