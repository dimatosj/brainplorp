"""
Main CLI entry point for plorp.

Refactored for v1.1 to use core functions directly.
"""

import json
from datetime import date
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from brainplorp import __version__
from brainplorp.config import load_config
from brainplorp.core import (
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
from brainplorp.core.process import process_daily_note_step1, process_daily_note_step2
from brainplorp.integrations.taskwarrior import get_tasks, TaskWarriorError, TaskWarriorTimeoutError
from brainplorp.utils.dates import format_date
from brainplorp.utils.prompts import confirm, prompt
from brainplorp.utils.taskwarrior_errors import handle_taskwarrior_error
from brainplorp.commands.setup import setup, configure_mcp_standalone
from brainplorp.commands.doctor import doctor

console = Console()


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx):
    """
    brainplorp - Workflow automation for TaskWarrior + Obsidian

    brainplorp helps you manage daily workflows by bridging TaskWarrior
    (task management) and Obsidian (note-taking).

    Key commands:
      doctor      - Diagnose system health and configuration issues
      setup       - Interactive setup wizard (run after install)
      mcp         - Configure Claude Desktop MCP integration
      start       - Generate daily note from TaskWarrior tasks
      tasks       - List pending tasks with filters (fast queries)
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

    except (TaskWarriorTimeoutError, TaskWarriorError) as e:
        handle_taskwarrior_error(e, "Generating daily note")
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

    except (TaskWarriorTimeoutError, TaskWarriorError) as e:
        handle_taskwarrior_error(e, "During review")
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
        # Sprint 8.5: Pass vault_path for State Sync
        mark_completed(task["uuid"], vault_path=vault_path)
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
            # Sprint 8.5: Pass vault_path for State Sync
            drop_task(task["uuid"], vault_path=vault_path)
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


@cli.group()
@click.pass_context
def inbox(ctx):
    """Inbox management (add, process, fetch)."""
    pass


@inbox.command("add")
@click.argument("text", nargs=-1, required=True)
@click.option("--urgent", "-u", is_flag=True, help="Mark as urgent (🔴)")
@click.pass_context
def inbox_add(ctx, text, urgent):
    """
    Quick-add item to inbox.

    Pure capture - no metadata. Use 'plorp inbox process' to assign projects and tags.
    Perfect for keyboard-driven workflows and fast thought capture.

    Examples:

        # Simple add
        plorp inbox add "Buy milk"

        # Multi-word items (no quotes needed)
        plorp inbox add Review PR #42 before EOD

        # Mark as urgent
        plorp inbox add "Call client ASAP" --urgent

    All project assignment, tagging, and due dates happen during 'plorp inbox process'.
    """
    from brainplorp.core.inbox import quick_add_to_inbox

    try:
        config = load_config()
        vault_path = Path(config["vault_path"]).expanduser().resolve()

        # Join text arguments
        text_str = " ".join(text)

        # Quick add
        result = quick_add_to_inbox(
            text=text_str,
            vault_path=vault_path,
            urgent=urgent
        )

        # Report success
        console.print(f"[green]✓ Added to inbox:[/green] {result['item']}")
        console.print(f"[dim]  {result['inbox_path']}[/dim]")

    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}", err=True)
        ctx.exit(1)


@inbox.command("process")
@click.pass_context
def inbox_process(ctx):
    """
    Process inbox items interactively.

    For each unprocessed item, choose to create a task, note, both, discard, or skip.
    This is where you assign projects, tags, due dates, and priorities.
    """
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

    except (TaskWarriorTimeoutError, TaskWarriorError) as e:
        handle_taskwarrior_error(e, "Processing inbox")
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


@inbox.command("fetch")
@click.option("--limit", default=20, help="Max emails to fetch")
@click.option("--label", default=None, help="Gmail label (default: INBOX)")
@click.option("--dry-run", is_flag=True, help="Show emails without appending")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed progress")
@click.pass_context
def inbox_fetch(ctx, limit, label, dry_run, verbose):
    """
    Fetch emails from Gmail and append to inbox.

    Requires email configuration in ~/.config/plorp/config.yaml:

      email:
        enabled: true
        username: your@gmail.com
        password: "app_password"

    Gmail App Password setup:
      1. Enable 2FA on Gmail
      2. Go to https://myaccount.google.com/apppasswords
      3. Generate password for "plorp"
      4. Copy 16-char password to config
    """
    from brainplorp.integrations.email_imap import (
        connect_gmail,
        fetch_unread_emails,
        convert_email_body_to_bullets,
        mark_emails_as_seen,
        disconnect,
    )
    from brainplorp.core.inbox import append_emails_to_inbox

    try:
        config = load_config()

        # Check email config
        if "email" not in config or not config["email"].get("enabled"):
            console.print("[red]❌ Email not configured[/red]")
            console.print(
                "[dim]Add email config to ~/.config/plorp/config.yaml[/dim]"
            )
            ctx.exit(1)

        email_config = config["email"]
        username = email_config.get("username")
        password = email_config.get("password")
        server = email_config.get("imap_server", "imap.gmail.com")
        port = email_config.get("imap_port", 993)
        folder = label or email_config.get("inbox_label", "INBOX")

        if not username or not password:
            console.print("[red]❌ Email username/password missing in config[/red]")
            ctx.exit(1)

        # Strip whitespace from password (PM Answer A10)
        password = password.replace(" ", "").replace("\n", "")

        if verbose:
            console.print(f"[dim]Connecting to {server}:{port}...[/dim]")

        # Connect to Gmail
        client = connect_gmail(username, password, server, port)

        if verbose:
            console.print(f"[dim]Fetching emails from {folder}...[/dim]")

        # Fetch emails
        emails = fetch_unread_emails(client, folder, limit)

        if not emails:
            console.print("[green]✓ No new emails[/green]")
            disconnect(client)
            return

        if verbose or dry_run:
            console.print(f"[yellow]📧 Found {len(emails)} new email(s)[/yellow]")
            for i, email in enumerate(emails, 1):
                # Preview first line of body (not subject, per PM Answer A9)
                body_preview = convert_email_body_to_bullets(
                    email["body_text"], email["body_html"]
                )
                first_line = (
                    body_preview.split("\n")[0][:60] if body_preview else "(empty)"
                )
                console.print(f"  {i}. {first_line}...")

        if dry_run:
            console.print("\n[dim]Dry run - not appending to inbox[/dim]")
            disconnect(client)
            return

        # Append to inbox
        vault_path = Path(config["vault_path"]).expanduser().resolve()
        result = append_emails_to_inbox(emails, vault_path)

        # Mark as seen
        email_ids = [e["id"] for e in emails]
        mark_emails_as_seen(client, email_ids)

        # Disconnect
        disconnect(client)

        # Report success
        console.print(f"[green]✓ Appended {result['appended_count']} email(s) to inbox[/green]")
        console.print(f"[dim]  Inbox: {result['inbox_path']}[/dim]")
        console.print(f"[dim]  Total unprocessed: {result['total_unprocessed']}[/dim]")

    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}", err=True)
        if verbose:
            import traceback

            console.print(f"[dim]{traceback.format_exc()}[/dim]")
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

    except (TaskWarriorTimeoutError, TaskWarriorError) as e:
        handle_taskwarrior_error(e, "Creating note")
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

    except (TaskWarriorTimeoutError, TaskWarriorError) as e:
        handle_taskwarrior_error(e, "Linking note")
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
            # Sprint 8.5: Pass vault_path for State Sync
            result = process_daily_note_step2(note_path, target_date, vault_path)

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

    except (TaskWarriorTimeoutError, TaskWarriorError) as e:
        handle_taskwarrior_error(e, "Processing daily note")
    except DailyNoteNotFoundError as e:
        console.print(f"[red]❌ Daily note not found for {e.date}[/red]")
        console.print(f"[dim]💡 Run 'plorp start --date {e.date}' first[/dim]")
        ctx.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error processing daily note:[/red] {str(e)}")
        console.print(f"[dim]Debug info: {type(e).__name__}[/dim]")
        ctx.exit(1)


@cli.command()
@click.option('--urgent', is_flag=True, help='Show only urgent (priority:H) tasks')
@click.option('--important', is_flag=True, help='Show important (priority:M) tasks')
@click.option('--project', help='Filter by project')
@click.option('--due', help='Filter by due date (today, tomorrow, overdue, week)')
@click.option('--limit', default=50, help='Limit number of results')
@click.option('--format', 'output_format', default='table', type=click.Choice(['table', 'simple', 'json']))
@click.pass_context
def tasks(ctx, urgent, important, project, due, limit, output_format):
    """
    List pending tasks with optional filters.

    Examples:
      plorp tasks                          # All pending tasks
      plorp tasks --urgent                 # Urgent only
      plorp tasks --project work           # Work project
      plorp tasks --due today              # Due today
      plorp tasks --overdue                # Overdue
      plorp tasks --urgent --project work  # Combine filters
    """
    try:
        config = load_config()

        # Build TaskWarrior filter
        filters = ['status:pending']

        if urgent:
            filters.append('priority:H')
        elif important:
            filters.append('priority:M')

        if project:
            filters.append(f'project:{project}')

        if due == 'today':
            filters.append('due:today')
        elif due == 'tomorrow':
            filters.append('due:tomorrow')
        elif due == 'overdue':
            filters.append('due.before:today')
        elif due == 'week':
            filters.append('due.before:eow')

        # Get tasks from TaskWarrior
        task_list = get_tasks(filters)

        # Limit results
        if len(task_list) > limit:
            task_list = task_list[:limit]

        # Format output
        if output_format == 'json':
            click.echo(json.dumps(task_list, indent=2))
        elif output_format == 'simple':
            for task in task_list:
                pri = task.get('priority', ' ')
                desc = task.get('description', '')
                proj = task.get('project', '')
                click.echo(f"[{pri}] {desc} ({proj})")
        else:  # table
            table = Table(title=f"Tasks ({len(task_list)})")

            table.add_column("Pri", width=6)
            table.add_column("Description", width=40)
            table.add_column("Project", width=15)
            table.add_column("Due", width=12)

            for task in task_list:
                pri = task.get('priority', '')
                pri_icon = '🔴' if pri == 'H' else '🟡' if pri == 'M' else '  '
                desc = task.get('description', '')
                proj = task.get('project', '')
                due_date = task.get('due', '')

                # Format due date
                if due_date:
                    due_date = format_date(due_date, format='short')

                table.add_row(f"{pri} [{pri_icon}]", desc, proj, due_date)

            console.print(table)

    except (TaskWarriorTimeoutError, TaskWarriorError) as e:
        handle_taskwarrior_error(e, "Listing tasks")
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}", err=True)
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
    from brainplorp.core.projects import create_project

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
    except (TaskWarriorTimeoutError, TaskWarriorError) as e:
        handle_taskwarrior_error(e, "Creating project")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)


@project.command("list")
@click.option("--domain", "-d", help="Filter by domain")
@click.option("--state", "-s", help="Filter by state")
@click.pass_context
def project_list(ctx, domain, state):
    """List projects."""
    from brainplorp.core.projects import list_projects

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
    from brainplorp.core.projects import get_project_info

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


@project.command("sync-all")
@click.pass_context
def project_sync_all(ctx):
    """Sync all project note bodies with frontmatter (Sprint 8.6).

    Bulk reconciliation command useful after:
    - External TaskWarrior changes (CLI, mobile apps)
    - TaskWarrior sync from other devices
    - Periodic state maintenance
    """
    config = load_config()
    vault_path = Path(config["vault_path"]).expanduser().resolve()

    from brainplorp.core.projects import sync_all_projects

    try:
        console.print("[yellow]🔄 Syncing all project notes...[/yellow]")
        stats = sync_all_projects(vault_path)

        console.print(f"[green]✅ Synced {stats['synced']} project(s)[/green]")

        if stats["errors"]:
            console.print(f"[red]❌ {len(stats['errors'])} error(s) occurred:[/red]")
            for project_path, error_msg in stats["errors"]:
                console.print(f"  {project_path}: {error_msg}")
            ctx.exit(1)

    except (TaskWarriorTimeoutError, TaskWarriorError) as e:
        handle_taskwarrior_error(e, "Syncing projects")
    except Exception as e:
        console.print(f"[red]❌ Error syncing projects:[/red] {e}")
        ctx.exit(1)


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
    from brainplorp.core.projects import set_focused_domain_cli

    set_focused_domain_cli(domain)
    click.echo(f"✓ Focused on domain: {domain}")


@focus.command("get")
@click.pass_context
def focus_get(ctx):
    """Get current focused domain."""
    from brainplorp.core.projects import get_focused_domain_cli

    domain = get_focused_domain_cli()
    click.echo(f"Current focus: {domain}")


# Register diagnostic command
cli.add_command(doctor)

# Register setup command
cli.add_command(setup)

# Register MCP configuration command
cli.add_command(configure_mcp_standalone, name="mcp")


@cli.group()
@click.pass_context
def config(ctx):
    """Configuration management commands."""
    pass


@config.command("validate")
@click.pass_context
def config_validate(ctx):
    """Validate brainplorp configuration."""
    from pathlib import Path
    import json
    import shutil

    cfg = load_config()
    errors = []
    warnings = []

    # Check vault path
    vault_path = Path(cfg['vault_path']) if 'vault_path' in cfg else None
    if not vault_path:
        errors.append("Vault path not configured")
    elif not vault_path.exists():
        errors.append(f"Vault path does not exist: {vault_path}")
    elif not (vault_path / '.obsidian').exists():
        warnings.append(f"Not an Obsidian vault (missing .obsidian): {vault_path}")

    # Check TaskWarrior
    if not shutil.which('task'):
        errors.append("TaskWarrior not installed (run: brew install task)")

    # Check MCP configuration
    claude_config_path = Path.home() / 'Library' / 'Application Support' / 'Claude' / 'claude_desktop_config.json'
    if claude_config_path.exists():
        with open(claude_config_path, 'r') as f:
            claude_config = json.load(f)

        if 'brainplorp' not in claude_config.get('mcpServers', {}):
            warnings.append("brainplorp MCP server not configured in Claude Desktop")
    else:
        warnings.append("Claude Desktop not installed or not configured")

    # Print results
    if errors:
        click.secho("❌ Configuration Errors:", fg='red', bold=True)
        for error in errors:
            click.echo(f"  • {error}")

    if warnings:
        click.secho("⚠️  Warnings:", fg='yellow', bold=True)
        for warning in warnings:
            click.echo(f"  • {warning}")

    if not errors and not warnings:
        click.secho("✅ Configuration valid!", fg='green', bold=True)

    return 0 if not errors else 1


@cli.group()
@click.pass_context
def vault(ctx):
    """Manage vault sync across devices."""
    pass


@vault.command('status')
@click.pass_context
def vault_status(ctx):
    """
    Show vault sync status.

    Displays sync status, detects conflicts, and shows last sync time.
    """
    config = ctx.obj['config']
    vault_path = Path(config.get('vault_path', ''))

    if not vault_path or not vault_path.exists():
        click.secho("⚠️  Vault path not configured or does not exist", fg='yellow')
        return

    vault_sync = config.get('vault_sync', {})

    if not vault_sync.get('enabled'):
        click.secho("❌ Vault sync not configured", fg='red')
        click.echo()
        click.echo("To configure vault sync:")
        click.echo("  1. Run 'brainplorp setup'")
        click.echo("  2. Choose 'Yes' for vault sync")
        click.echo()
        return

    # Display sync status
    click.echo("Vault Sync Status")
    click.echo("━" * 60)
    click.echo()

    click.echo(f"  Status: ✓ Configured")
    click.echo(f"  Server: {vault_sync.get('server')}")
    click.echo(f"  Database: {vault_sync.get('database')}")
    click.echo(f"  Username: {vault_sync.get('username')}")
    click.echo()

    # Check for conflicts
    conflicts = list(vault_path.rglob("*.conflicted.md"))

    if conflicts:
        click.echo()
        click.secho("⚠️  Conflicts detected:", fg='yellow', bold=True)
        for conflict_file in conflicts:
            original = str(conflict_file).replace('.conflicted.md', '.md')
            relative_path = conflict_file.relative_to(vault_path)
            click.echo(f"   • {relative_path.parent / conflict_file.stem}.md")

        click.echo()
        click.echo("Resolve conflicts:")
        click.echo("  1. Open conflicted file in Obsidian")
        click.echo("  2. Merge changes manually")
        click.echo("  3. Delete .conflicted.md file")
        click.echo()
    else:
        click.echo("  ✓ No conflicts detected")
        click.echo()

    # Instructions for other computers
    if vault_sync.get('enabled'):
        click.echo("To sync on another computer:")
        click.echo("  1. Install brainplorp on the new computer")
        click.echo("  2. Run 'brainplorp setup'")
        click.echo("  3. Enter these credentials when prompted:")
        click.echo(f"     Server:   {vault_sync.get('server')}")
        click.echo(f"     Database: {vault_sync.get('database')}")
        click.echo(f"     Username: {vault_sync.get('username')}")
        click.echo("     Password: [from your first computer]")
        click.echo()


if __name__ == "__main__":
    cli()
