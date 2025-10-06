# ABOUTME: Main CLI entry point using Click framework - defines all plorp commands
# ABOUTME: Handles command routing, help text, and version display for the plorp tool
"""
Main CLI entry point for plorp.
"""
import click
from plorp import __version__
from plorp.config import load_config


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx):
    """
    plorp - Workflow automation for TaskWarrior + Obsidian

    plorp helps you manage daily workflows by bridging TaskWarrior
    (task management) and Obsidian (note-taking).

    Key commands:
      start   - Generate daily note from TaskWarrior tasks
      review  - Interactive end-of-day task review
      inbox   - Process inbox items into tasks/notes
    """
    ctx.ensure_object(dict)


@cli.command()
@click.pass_context
def start(ctx):
    """Generate daily note for today."""
    config = load_config()

    try:
        from plorp.workflows.daily import start as daily_start

        note_path = daily_start(config)
        # Output already printed by daily_start()
    except FileExistsError as e:
        click.echo(str(e), err=True)
        ctx.exit(1)
    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        click.echo(
            f"💡 Make sure vault directory exists: {config.get('vault_path')}",
            err=True,
        )
        ctx.exit(1)
    except Exception as e:
        click.echo(f"❌ Error generating daily note: {e}", err=True)
        import traceback

        traceback.print_exc()
        ctx.exit(1)


@cli.command()
def review():
    """Interactive end-of-day review."""
    click.echo("⚠️  'review' command not yet implemented (coming in a future sprint)")


@cli.command()
def inbox():
    """Process inbox items."""
    click.echo("⚠️  'inbox' command not yet implemented (coming in a future sprint)")


if __name__ == "__main__":
    cli()
