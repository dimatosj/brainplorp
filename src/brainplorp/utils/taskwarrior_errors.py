"""
Common error handling for TaskWarrior operations.

Provides consistent error messages and recovery instructions
when TaskWarrior operations fail or timeout.
"""

import sys
import click


def handle_taskwarrior_error(error: Exception, context: str = "TaskWarrior operation"):
    """
    Common error handler for TaskWarrior exceptions.

    Displays user-friendly error messages with actionable fix instructions
    and exits with appropriate status code.

    Args:
        error: The exception raised (TaskWarriorTimeoutError or TaskWarriorError)
        context: Description of what was being attempted (e.g., "Fetching tasks")

    Exits:
        1 - Operation failed, user should take action
    """
    # Import here to avoid circular dependency
    from brainplorp.integrations.taskwarrior import TaskWarriorTimeoutError, TaskWarriorError

    if isinstance(error, TaskWarriorTimeoutError):
        click.secho(f"✗ {context} timed out", fg='red', bold=True)
        click.echo()
        click.echo(str(error))
        click.echo()
        click.secho("This usually indicates TaskWarrior is hanging.", fg='yellow')
        click.echo("Common causes:")
        click.echo("  • TaskWarrior 3.4.1 has a known hang bug")
        click.echo("  • Corrupted TaskWarrior database")
        click.echo()
        click.secho("Recommended fix:", fg='green', bold=True)
        click.echo("  1. Run: brainplorp doctor")
        click.echo("  2. Follow the fix instructions provided")
        click.echo()
        sys.exit(1)
    elif isinstance(error, TaskWarriorError):
        click.secho(f"✗ {context} failed", fg='red', bold=True)
        click.echo()
        click.echo(str(error))
        click.echo()
        click.secho("Recommended fix:", fg='green', bold=True)
        click.echo("  1. Run: brainplorp doctor")
        click.echo("  2. Check TaskWarrior installation: task --version")
        click.echo()
        sys.exit(1)
    else:
        # Unexpected error - re-raise
        raise error
