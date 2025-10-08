"""
Main CLI entry point for plorp.

Refactored for v1.1 to use core functions directly.
"""

from datetime import date
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from plorp import __version__
from plorp.config import load_config
from plorp.core import (
    start_day,
    get_review_tasks,
    add_review_notes,
    mark_completed,
    defer_task,
    drop_task,
    set_priority,
    get_inbox_items,
    create_task_from_inbox,
    create_note_from_inbox,
    create_both_from_inbox,
    discard_inbox_item,
    create_note_standalone,
    create_note_linked_to_task,
    link_note_to_task,
    # Exceptions
    PlorpError,
    VaultNotFoundError,
    DailyNoteExistsError,
    DailyNoteNotFoundError,
    TaskNotFoundError,
    InboxNotFoundError,
)
from plorp.core.process import process_daily_note_step1, process_daily_note_step2
from plorp.utils.prompts import confirm, prompt

console = Console()


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx):
    """
    plorp - Workflow automation for TaskWarrior + Obsidian

    plorp helps you manage daily workflows by bridging TaskWarrior
    (task management) and Obsidian (note-taking).

    Key commands:
      start       - Generate daily note from TaskWarrior tasks
      process     - Process informal tasks with NLP (Sprint 7)
      review      - Interactive end-of-day task review
      inbox       - Process inbox items into tasks/notes
      note        - Create notes (optionally linked to tasks)
      link        - Link existing note to task
      init-claude - Install slash commands for Claude Desktop
    """
    ctx.ensure_object(dict)


@cli.command()
@click.option("--date", "date_str", default=None, help="Date for daily note (YYYY-MM-DD, defaults to today)")
@click.pass_context
def start(ctx, date_str):
    """Generate daily note for today."""
    config = load_config()
    vault_path = Path(config["vault_path"]).expanduser().resolve()

    # Parse date
    target_date = date.fromisoformat(date_str) if date_str else date.today()

    try:
        result = start_day(target_date, vault_path)

        # Display summary
        console.print(f"[green]✅ Created daily note:[/green] {result['note_path']}")
        console.print()

        summary = result["summary"]
        console.print(f"[yellow]📊 Task Summary:[/yellow]")
        console.print(f"  Overdue: {summary['overdue_count']}")
        console.print(f"  Due today: {summary['due_today_count']}")
        console.print(f"  Recurring: {summary['recurring_count']}")
        console.print(f"  [bold]Total: {summary['total_count']}[/bold]")

    except DailyNoteExistsError as e:
        console.print(f"[red]❌ Daily note already exists:[/red] {e.note_path}")
        console.print("[dim]💡 Tip: Open the existing note or delete it first[/dim]")
        ctx.exit(1)
    except VaultNotFoundError as e:
        console.print(f"[red]❌ Vault not found:[/red] {e.vault_path}")
        console.print(
            f"[dim]💡 Check vault_path in ~/.config/plorp/config.yaml[/dim]"        )
        ctx.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error generating daily note:[/red] {e}")
        ctx.exit(1)


@cli.command()
@click.option("--date", "date_str", default=None, help="Date to review (YYYY-MM-DD, defaults to today)")
@click.pass_context
def review(ctx, date_str):
    """Interactive end-of-day review."""
    config = load_config()
    vault_path = Path(config["vault_path"]).expanduser().resolve()

    target_date = date.fromisoformat(date_str) if date_str else date.today()

    try:
        # Get uncompleted tasks
        review_data = get_review_tasks(target_date, vault_path)

        if review_data["uncompleted_count"] == 0:
            console.print("[green]🎉 All tasks completed![/green]")
            _add_review_reflection(target_date, vault_path)
            return

        console.print(
            f"[yellow]Found {review_data['uncompleted_count']} uncompleted task(s)[/yellow]"
        )
        console.print()

        # Process each uncompleted task
        for task in review_data["uncompleted_tasks"]:
            _review_task(task, vault_path)

        # Add review notes
        _add_review_reflection(target_date, vault_path)

        console.print("[green]✅ Review complete![/green]")

    except DailyNoteNotFoundError as e:
        console.print(f"[red]❌ No daily note found for {e.date}[/red]")
        console.print("[dim]💡 Run 'plorp start' first[/dim]")
        ctx.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Review interrupted[/yellow]")
        ctx.exit(0)
    except Exception as e:
        console.print(f"[red]❌ Error during review:[/red] {e}")
        ctx.exit(1)


def _review_task(task, vault_path):
    """Interactive review of a single task."""
    console.print(f"[bold cyan]Task:[/bold cyan] {task['description']}")

    if task.get("status") == "missing":
        console.print("[red]⚠️  Task deleted from TaskWarrior[/red]")
        return

    if task.get("project"):
        console.print(f"  Project: {task['project']}")
    if task.get("due"):
        console.print(f"  Due: {task['due']}")
    if task.get("priority"):
        console.print(f"  Priority: {task['priority']}")

    console.print()

    # Prompt for action
    action = prompt(
        "Action? [d]one, de[f]er, [p]riority, [x]delete, [s]kip",
        default="s",
    )

    if action == "d":
        mark_completed(task["uuid"])
        console.print("[green]✓ Marked complete[/green]")
    elif action == "f":
        new_due = prompt("New due date (YYYY-MM-DD)")
        defer_task(task["uuid"], date.fromisoformat(new_due))
        console.print(f"[yellow]→ Deferred to {new_due}[/yellow]")
    elif action == "p":
        priority = prompt("Priority (H/M/L or empty for none)", default="")
        set_priority(task["uuid"], priority)
        console.print(f"[yellow]Priority set to {priority or 'none'}[/yellow]")
    elif action == "x":
        if confirm("Really delete this task?", default=False):
            drop_task(task["uuid"])
            console.print("[red]✗ Deleted[/red]")
    elif action == "s":
        console.print("[dim]Skipped[/dim]")

    console.print()


def _add_review_reflection(target_date, vault_path):
    """Add review reflection notes."""
    console.print("[bold]End of day reflection:[/bold]")

    went_well = prompt("What went well today? (optional)", default="")
    could_improve = prompt("What could improve? (optional)", default="")
    tomorrow = prompt("Notes for tomorrow? (optional)", default="")

    if went_well or could_improve or tomorrow:
        reflections = {
            "went_well": went_well,
            "could_improve": could_improve,
            "tomorrow": tomorrow,
        }
        add_review_notes(target_date, vault_path, reflections)
        console.print("[green]✓ Review notes saved[/green]")


@cli.command()
@click.argument("subcommand", default="process")
@click.pass_context
def inbox(ctx, subcommand):
    """Process inbox items."""
    if subcommand != "process":
        console.print(f"[red]❌ Unknown inbox subcommand:[/red] {subcommand}")
        console.print("[dim]💡 Available: plorp inbox process[/dim]")
        ctx.exit(1)

    config = load_config()
    vault_path = Path(config["vault_path"]).expanduser().resolve()

    try:
        inbox_data = get_inbox_items(vault_path)

        if inbox_data["item_count"] == 0:
            console.print("[green]✅ Inbox is empty![/green]")
            return

        console.print(f"[yellow]Found {inbox_data['item_count']} inbox item(s)[/yellow]")
        console.print()

        for item in inbox_data["unprocessed_items"]:
            _process_inbox_item(item, vault_path)

        console.print("[green]✅ Inbox processing complete![/green]")

    except InboxNotFoundError as e:
        console.print(f"[red]❌ Inbox not found:[/red] {e.inbox_path}")
        console.print("[dim]💡 Create inbox file first[/dim]")
        ctx.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Inbox processing interrupted[/yellow]")
        ctx.exit(0)
    except Exception as e:
        console.print(f"[red]❌ Error processing inbox:[/red] {e}")
        ctx.exit(1)


def _process_inbox_item(item, vault_path):
    """Process a single inbox item interactively."""
    console.print(f"[bold cyan]Item:[/bold cyan] {item['text']}")
    console.print()

    action = prompt("Action? [t]ask, [n]ote, [b]oth, [d]iscard, [s]kip", default="s")

    if action == "t":
        description = prompt("Task description", default=item["text"])
        due = prompt("Due date (YYYY-MM-DD, optional)", default="")
        priority = prompt("Priority (H/M/L, optional)", default="")
        project = prompt("Project (optional)", default="")

        create_task_from_inbox(
            vault_path,
            item["text"],
            description,
            due=due or None,
            priority=priority or None,
            project=project or None,
        )
        console.print("[green]✓ Created task[/green]")

    elif action == "n":
        title = prompt("Note title")
        content = prompt("Note content (optional)", default="")

        create_note_from_inbox(vault_path, item["text"], title, content=content)
        console.print("[green]✓ Created note[/green]")

    elif action == "b":
        task_desc = prompt("Task description", default=item["text"])
        note_title = prompt("Note title")
        note_content = prompt("Note content (optional)", default="")
        due = prompt("Due date (YYYY-MM-DD, optional)", default="")
        priority = prompt("Priority (H/M/L, optional)", default="")
        project = prompt("Project (optional)", default="")

        create_both_from_inbox(
            vault_path,
            item["text"],
            task_desc,
            note_title,
            note_content=note_content,
            due=due or None,
            priority=priority or None,
            project=project or None,
        )
        console.print("[green]✓ Created task and note[/green]")

    elif action == "d":
        if confirm("Discard this item?", default=False):
            discard_inbox_item(vault_path, item["text"])
            console.print("[red]✗ Discarded[/red]")

    elif action == "s":
        console.print("[dim]Skipped[/dim]")

    console.print()


@cli.command()
@click.argument("title")
@click.option("--task", default=None, help="Task UUID to link to note")
@click.option("--type", default="general", help="Note type (general, meeting, project)")
@click.pass_context
def note(ctx, title, task, type):
    """Create a new note, optionally linked to a task."""
    config = load_config()
    vault_path = Path(config["vault_path"]).expanduser().resolve()

    try:
        if task:
            result = create_note_linked_to_task(vault_path, title, task, note_type=type)
            console.print(f"[green]✅ Created note:[/green] {result['note_path']}")
            console.print(f"[cyan]🔗 Linked to task:[/cyan] {task}")
        else:
            result = create_note_standalone(vault_path, title, note_type=type)
            console.print(f"[green]✅ Created note:[/green] {result['note_path']}")

    except TaskNotFoundError as e:
        console.print(f"[red]❌ Task not found:[/red] {e.uuid}")
        ctx.exit(1)
    except VaultNotFoundError as e:
        console.print(f"[red]❌ Vault not found:[/red] {e.vault_path}")
        ctx.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error creating note:[/red] {e}")
        ctx.exit(1)


@cli.command()
@click.argument("task_uuid")
@click.argument("note_path")
@click.pass_context
def link(ctx, task_uuid, note_path):
    """Link an existing note to a task."""
    config = load_config()
    vault_path = Path(config["vault_path"]).expanduser().resolve()
    note = Path(note_path)

    # Handle relative paths
    if not note.is_absolute():
        note = vault_path / note

    try:
        result = link_note_to_task(vault_path, note, task_uuid)

        console.print("[green]✅ Linked note to task[/green]")
        console.print(f"[dim]📝 Note:[/dim] {note}")
        console.print(f"[dim]📋 Task:[/dim] {task_uuid}")

    except TaskNotFoundError as e:
        console.print(f"[red]❌ Task not found:[/red] {e.uuid}")
        ctx.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error linking note:[/red] {e}")
        ctx.exit(1)


@cli.command("init-claude")
@click.option("--force", is_flag=True, help="Overwrite existing slash commands")
@click.pass_context
def init_claude(ctx, force):
    """Install slash commands for Claude Desktop."""
    import shutil

    # Source slash commands directory
    slash_commands_src = Path(__file__).parent / "slash_commands"

    if not slash_commands_src.exists():
        console.print(
            "[red]❌ Slash commands not found in plorp installation[/red]"        )
        ctx.exit(1)

    # Destination directory
    claude_commands_dir = Path.home() / ".claude" / "commands"
    claude_commands_dir.mkdir(parents=True, exist_ok=True)

    # Copy each slash command
    copied = 0
    skipped = 0

    for src_file in slash_commands_src.glob("*.md"):
        dest_file = claude_commands_dir / src_file.name

        if dest_file.exists() and not force:
            console.print(f"[yellow]⊘ Skipping (exists):[/yellow] {src_file.name}")
            skipped += 1
        else:
            shutil.copy2(src_file, dest_file)
            console.print(f"[green]✓ Installed:[/green] {src_file.name}")
            copied += 1

    console.print()
    console.print(f"[bold]Summary:[/bold] {copied} installed, {skipped} skipped")

    if skipped > 0 and not force:
        console.print("[dim]💡 Use --force to overwrite existing commands[/dim]")


@cli.command()
@click.option("--date", "date_str", default=None, help="Date for daily note to process (YYYY-MM-DD, defaults to today)")
@click.pass_context
def process(ctx, date_str):
    """
    Process informal tasks in daily note.

    Step 1 (no TBD section): Scan daily note for informal tasks (checkboxes without UUIDs),
    generate proposals with natural language parsing, and add to TBD section.

    Step 2 (TBD section exists): Create TaskWarrior tasks from approved [Y] proposals,
    reorganize note, and remove TBD section (unless errors exist).
    """
    config = load_config()
    vault_path = Path(config["vault_path"]).expanduser().resolve()

    # Parse date
    target_date = date.fromisoformat(date_str) if date_str else date.today()

    # Construct daily note path
    daily_dir = vault_path / "daily"
    note_path = daily_dir / f"{target_date}.md"

    try:
        if not note_path.exists():
            console.print(f"[red]❌ Daily note not found:[/red] {note_path}")
            console.print(f"[dim]💡 Run 'plorp start' to create today's note first[/dim]")
            ctx.exit(1)

        # Check if TBD section exists to determine which step to run
        content = note_path.read_text()
        has_tbd_section = "## TBD Processing" in content

        if has_tbd_section:
            # Run Step 2: Create tasks from approvals
            result = process_daily_note_step2(note_path, target_date)

            # Display summary
            console.print(f"[green]✅ Processed approvals:[/green] {note_path}")
            console.print()

            if result["approved_count"] == 0:
                console.print("[yellow]📋 No approved tasks found[/yellow]")
                console.print("[dim]💡 Mark tasks with [Y] in ## TBD Processing section[/dim]")
                return

            console.print(f"[green]✅ Created {len(result['created_tasks'])} task(s) in TaskWarrior[/green]")

            if result["rejected_count"] > 0:
                console.print(f"[yellow]❌ Rejected {result['rejected_count']} task(s) (kept in original location)[/yellow]")

            if len(result["errors"]) > 0:
                console.print(f"[red]⚠️  {len(result['errors'])} error(s) occurred[/red]")
                console.print("[dim]   (Check TBD section for NEEDS_REVIEW items)[/dim]")

            if result["needs_review_remaining"]:
                console.print()
                console.print("[red]⚠️  TBD section kept - fix NEEDS_REVIEW items and run again[/red]")
            else:
                console.print()
                console.print("[bold]✅ All tasks processed - TBD section removed[/bold]")

        else:
            # Run Step 1: Generate proposals
            result = process_daily_note_step1(note_path, target_date)

            # Display summary
            console.print(f"[green]✅ Scanned daily note:[/green] {note_path}")
            console.print()

            if result["proposals_count"] == 0:
                console.print("[yellow]📋 No informal tasks found[/yellow]")
                console.print("[dim]💡 Informal tasks are checkboxes without UUIDs[/dim]")
                return

            console.print(f"[yellow]📊 Found {result['proposals_count']} informal task(s)[/yellow]")

            if result["needs_review_count"] > 0:
                console.print(f"[red]⚠️  {result['needs_review_count']} task(s) need review[/red]")
                console.print("[dim]   (Could not parse date - check TBD section)[/dim]")

            console.print()
            console.print("[bold]✅ Added proposals to ## TBD Processing section[/bold]")
            console.print()
            console.print("[dim]Next steps:[/dim]")
            console.print("  1. Open your daily note")
            console.print("  2. Review each proposal in ## TBD Processing")
            console.print("  3. Mark [Y] to approve or [N] to reject")
            console.print("  4. Run 'plorp process' again to create tasks")

    except DailyNoteNotFoundError as e:
        console.print(f"[red]❌ Daily note not found for {e.date}[/red]")
        console.print(f"[dim]💡 Run 'plorp start --date {e.date}' first[/dim]")
        ctx.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error processing daily note:[/red] {str(e)}")
        console.print(f"[dim]Debug info: {type(e).__name__}[/dim]")
        ctx.exit(1)



# ============================================================================
# Project Management Commands (Sprint 8)
# ============================================================================


@cli.group()
@click.pass_context
def project(ctx):
    """Project management commands."""
    pass


@project.command("create")
@click.argument("name")
@click.option("--domain", "-d", default="work", help="Domain (work/home/personal)")
@click.option("--workstream", "-w", help="Workstream")
@click.option("--state", "-s", default="active", help="State")
@click.option("--description", help="Project description")
@click.pass_context
def project_create(ctx, name, domain, workstream, state, description):
    """Create a new project."""
    from plorp.core.projects import create_project

    try:
        project = create_project(
            name=name,
            domain=domain,
            workstream=workstream,
            state=state,
            description=description
        )
        click.echo(f"✓ Created project: {project['full_path']}")
        click.echo(f"  Note: {project['note_path']}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)


@project.command("list")
@click.option("--domain", "-d", help="Filter by domain")
@click.option("--state", "-s", help="Filter by state")
@click.pass_context
def project_list(ctx, domain, state):
    """List projects."""
    from plorp.core.projects import list_projects

    result = list_projects(domain=domain, state=state)

    if not result["projects"]:
        click.echo("No projects found.")
        return

    click.echo(f"\n{len(result['projects'])} project(s):\n")
    for p in result["projects"]:
        click.echo(f"  {p['full_path']} [{p['state']}]")
        if p.get("description"):
            click.echo(f"    {p['description']}")


@project.command("info")
@click.argument("full_path")
@click.pass_context
def project_info(ctx, full_path):
    """Show project details."""
    from plorp.core.projects import get_project_info

    project = get_project_info(full_path)

    if not project:
        click.echo(f"Error: Project not found: {full_path}", err=True)
        ctx.exit(1)

    click.echo(f"\nProject: {project['full_path']}")
    click.echo(f"Domain: {project['domain']}")
    if project.get("workstream"):
        click.echo(f"Workstream: {project['workstream']}")
    click.echo(f"State: {project['state']}")
    if project.get("description"):
        click.echo(f"Description: {project['description']}")
    click.echo(f"Tasks: {len(project['task_uuids'])}")
    click.echo(f"Note: {project['note_path']}")


@cli.group()
@click.pass_context
def focus(ctx):
    """Domain focus management."""
    pass


@focus.command("set")
@click.argument("domain", type=click.Choice(["work", "home", "personal"]))
@click.pass_context
def focus_set(ctx, domain):
    """Set focused domain."""
    from plorp.core.projects import set_focused_domain_cli

    set_focused_domain_cli(domain)
    click.echo(f"✓ Focused on domain: {domain}")


@focus.command("get")
@click.pass_context
def focus_get(ctx):
    """Get current focused domain."""
    from plorp.core.projects import get_focused_domain_cli

    domain = get_focused_domain_cli()
    click.echo(f"Current focus: {domain}")


if __name__ == "__main__":
    cli()
