# ABOUTME: TaskWarrior 3.x integration layer using subprocess to call the 'task' CLI
# ABOUTME: Provides Python functions for all CRUD operations on tasks with proper error handling
"""
TaskWarrior Integration Module

This module provides a Python interface to TaskWarrior 3.x via subprocess calls.
All write operations use the 'task' CLI to ensure proper transaction handling.

Key functions:
- run_task_command(): Low-level subprocess wrapper
- get_tasks(): Query tasks with filters
- get_task_info(): Get single task by UUID
- create_task(): Create new task and return UUID
- mark_done(), defer_task(), set_priority(), delete_task(): Task modifications
- add_annotation(), get_task_annotations(): Task annotations for note linking
"""
import subprocess
import json
import sys
import re
import time
from typing import List, Dict, Any, Optional
from subprocess import CompletedProcess


def run_task_command(args: List[str], capture: bool = True) -> CompletedProcess:
    """
    Run a TaskWarrior command via subprocess.

    Args:
        args: Command arguments (without 'task' prefix)
        capture: Whether to capture output (False for interactive commands)

    Returns:
        CompletedProcess object with returncode, stdout, stderr

    Example:
        run_task_command(['export']) -> runs 'task export'
        run_task_command(['1', 'done'], capture=False) -> runs 'task 1 done' interactively
    """
    cmd = ["task"] + args

    if capture:
        result = subprocess.run(cmd, capture_output=True, text=True)
    else:
        result = subprocess.run(cmd)

    return result


def get_tasks(filters: List[str]) -> List[Dict[str, Any]]:
    """
    Get tasks matching filter criteria.

    Args:
        filters: List of TaskWarrior filter terms (e.g., ['status:pending', 'due:today'])

    Returns:
        List of task dictionaries (from JSON export), or [] on error

    Example:
        get_tasks(['status:pending', 'project:plorp'])
    """
    args = filters + ["export"]
    result = run_task_command(args, capture=True)

    if result.returncode != 0:
        print(f"Error getting tasks: {result.stderr}", file=sys.stderr)
        return []

    try:
        tasks = json.loads(result.stdout)
        return tasks
    except json.JSONDecodeError as e:
        print(f"Error parsing task JSON: {e}", file=sys.stderr)
        return []


def get_overdue_tasks() -> List[Dict[str, Any]]:
    """
    Get all overdue tasks.

    Returns:
        List of overdue task dictionaries
    """
    return get_tasks(["status:pending", "due.before:today"])


def get_due_today() -> List[Dict[str, Any]]:
    """
    Get all tasks due today.

    Returns:
        List of tasks due today
    """
    return get_tasks(["status:pending", "due:today"])


def get_recurring_today() -> List[Dict[str, Any]]:
    """
    Get all recurring tasks due today.

    Returns:
        List of recurring tasks due today
    """
    return get_tasks(["status:pending", "recur.any:", "due:today"])


def get_task_info(uuid: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific task.

    Args:
        uuid: Task UUID

    Returns:
        Task dictionary or None if not found

    Example:
        task = get_task_info('a1b2c3d4-e5f6-7890-1234-567890abcdef')
    """
    tasks = get_tasks([uuid])

    if tasks:
        return tasks[0]
    return None


def create_task(
    description: str,
    project: Optional[str] = None,
    due: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Optional[str]:
    """
    Create a new task in TaskWarrior.

    Args:
        description: Task description
        project: Project name (optional)
        due: Due date in TaskWarrior format (optional, e.g., 'friday', '2025-10-15')
        priority: Priority level (optional, H/M/L)
        tags: List of tags (optional)

    Returns:
        UUID of created task, or None on failure

    Example:
        uuid = create_task("Write tests", project="plorp", due="friday", tags=["dev"])
    """
    args = ["add", description]

    if project:
        args.append(f"project:{project}")
    if due:
        args.append(f"due:{due}")
    if priority:
        args.append(f"priority:{priority}")
    if tags:
        for tag in tags:
            args.append(f"+{tag}")

    result = run_task_command(args, capture=True)

    if result.returncode != 0:
        print(f"Error creating task: {result.stderr}", file=sys.stderr)
        return None

    # Parse "Created task N." from stdout
    match = re.search(r"Created task (\d+)\.", result.stdout)
    if not match:
        print(f"Error: Could not parse task ID from output: {result.stdout}", file=sys.stderr)
        return None

    task_id = match.group(1)

    # Query by ID to get UUID with retry logic to handle race conditions
    # TaskWarrior 3.x SQLite may not have committed immediately after task creation
    max_attempts = 3
    delay = 0.05  # 50ms

    for attempt in range(max_attempts):
        export_result = run_task_command([task_id, "export"], capture=True)

        if export_result.returncode == 0:
            try:
                tasks = json.loads(export_result.stdout)
                if tasks:
                    return tasks[0]["uuid"]
            except json.JSONDecodeError:
                pass

        # Retry with exponential backoff
        if attempt < max_attempts - 1:
            time.sleep(delay)
            delay *= 2  # Exponential backoff: 50ms, 100ms

    # Final fallback after all retries
    print(f"Error: Could not retrieve UUID for task {task_id} after {max_attempts} attempts", file=sys.stderr)
    return None


def mark_done(uuid: str) -> bool:
    """
    Mark a task as done.

    Args:
        uuid: Task UUID

    Returns:
        True on success, False on failure
    """
    result = run_task_command([uuid, "done"], capture=True)

    if result.returncode != 0:
        print(f"Error marking task done: {result.stderr}", file=sys.stderr)
        return False

    return True


def defer_task(uuid: str, new_due: str) -> bool:
    """
    Defer a task to a new due date.

    Args:
        uuid: Task UUID
        new_due: New due date in TaskWarrior format (e.g., 'tomorrow', '2025-10-15')

    Returns:
        True on success, False on failure
    """
    result = run_task_command([uuid, "modify", f"due:{new_due}"], capture=True)

    if result.returncode != 0:
        print(f"Error deferring task: {result.stderr}", file=sys.stderr)
        return False

    return True


def set_priority(uuid: str, priority: str) -> bool:
    """
    Set task priority.

    Args:
        uuid: Task UUID
        priority: Priority level (H/M/L)

    Returns:
        True on success, False on failure
    """
    result = run_task_command([uuid, "modify", f"priority:{priority}"], capture=True)

    if result.returncode != 0:
        print(f"Error setting priority: {result.stderr}", file=sys.stderr)
        return False

    return True


def delete_task(uuid: str) -> bool:
    """
    Delete a task.

    Args:
        uuid: Task UUID

    Returns:
        True on success, False on failure
    """
    result = run_task_command([uuid, "delete"], capture=True)

    if result.returncode != 0:
        print(f"Error deleting task: {result.stderr}", file=sys.stderr)
        return False

    return True


def modify_task(uuid: str, **kwargs) -> bool:
    """
    Modify task properties (generic modification function).

    Args:
        uuid: Task UUID
        **kwargs: Task properties to modify (project, due, priority, description, etc.)

    Returns:
        True on success, False on failure

    Example:
        modify_task(uuid, project="work.engineering.api", priority="H")
        modify_task(uuid, due="tomorrow", description="Updated description")
    """
    args = [uuid, "modify"]

    for key, value in kwargs.items():
        if value is None:
            # Skip None values
            continue
        args.append(f"{key}:{value}")

    result = run_task_command(args, capture=True)

    if result.returncode != 0:
        print(f"Error modifying task: {result.stderr}", file=sys.stderr)
        return False

    return True


def add_annotation(uuid: str, annotation: str) -> bool:
    """
    Add an annotation to a task.

    Args:
        uuid: Task UUID
        annotation: Annotation text (e.g., "Note: vault/notes/meeting.md")

    Returns:
        True on success, False on failure
    """
    result = run_task_command([uuid, "annotate", annotation], capture=True)

    if result.returncode != 0:
        print(f"Error adding annotation: {result.stderr}", file=sys.stderr)
        return False

    return True


def get_task_annotations(uuid: str) -> List[str]:
    """
    Get all annotations for a task.

    Args:
        uuid: Task UUID

    Returns:
        List of annotation strings (just the description text), or [] if none or error
    """
    task = get_task_info(uuid)

    if not task:
        return []

    annotations = task.get("annotations", [])
    return [ann["description"] for ann in annotations]
