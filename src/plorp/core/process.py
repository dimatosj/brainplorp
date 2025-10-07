# ABOUTME: Core task processing workflow - scan informal tasks, generate proposals, create tasks
# ABOUTME: Implements Sprint 7 two-step process: Step 1 (proposals) → Step 2 (task creation)
"""
Task Processing Core Module (Sprint 7).

Provides two-step workflow for processing informal tasks:
1. Scan daily note → generate proposals → create TBD section
2. Parse approvals → create TaskWarrior tasks → reorganize note
"""
import re
from datetime import date
from pathlib import Path
from typing import List

from plorp.core.types import (
    InformalTask,
    TaskProposal,
    ProcessStepOneResult,
    ProcessStepTwoResult,
    ProcessError,
    TaskInfo,
)
from plorp.parsers.nlp import (
    parse_due_date,
    parse_priority_keywords,
    extract_clean_description,
)


def scan_for_informal_tasks(content: str) -> List[InformalTask]:
    """
    Scan entire document for informal tasks (checkboxes without UUIDs).

    Args:
        content: Markdown content to scan

    Returns:
        List of InformalTask objects with metadata

    Implementation per Q9 (liberal detection):
        - Accept `-` or `*` bullets
        - Accept flexible spacing
        - Accept `[ ]`, `[x]`, `[X]` checkboxes
        - Capture line number (0-indexed, Q22)
        - Capture section name (Q10)
        - Capture original line (Q21)
    """
    informal_tasks: List[InformalTask] = []
    lines = content.split("\n")

    # Track current section for context
    current_section = "(top of file)"

    for line_num, line in enumerate(lines):
        # Update current section when we see headings (only ## or deeper, not top-level #)
        heading_match = re.match(r"^(#{2,6})\s+(.+)", line)
        if heading_match:
            current_section = heading_match.group(2).strip()
            continue

        # Detect checkboxes (liberal pattern per Q9)
        # Pattern: optional whitespace, dash or asterisk, optional space, checkbox (with optional space inside), text
        checkbox_match = re.match(r"^(\s*)[-*]\s*\[\s*([ xX]?)\s*\]\s+(.+)", line)

        if checkbox_match:
            indentation = checkbox_match.group(1)
            checkbox_char = checkbox_match.group(2)
            task_text = checkbox_match.group(3)

            # Ignore tasks with UUIDs (formal tasks, per Q4)
            if "uuid:" in task_text.lower():
                continue

            # Preserve original checkbox state (don't normalize case, Q19)
            if checkbox_char.strip() == "":
                checkbox_state = "[ ]"
            elif checkbox_char.upper() == "X":
                checkbox_state = f"[{checkbox_char}]"  # Preserve X or x
            else:
                checkbox_state = "[ ]"

            # Create InformalTask
            informal_task: InformalTask = {
                "text": task_text,
                "line_number": line_num,  # 0-indexed internally (Q22)
                "section": current_section,
                "checkbox_state": checkbox_state,
                "original_line": line,  # Complete original line for removal (Q21)
            }

            informal_tasks.append(informal_task)

    return informal_tasks


def generate_proposal(informal_task: InformalTask, reference_date: date) -> TaskProposal:
    """
    Analyze task text and generate TaskWarrior metadata proposal.

    Args:
        informal_task: Informal task to analyze
        reference_date: Reference date for relative date parsing

    Returns:
        TaskProposal with proposed metadata

    Implementation:
        - Parse due date with NLP (Q12, Q13)
        - Parse priority keywords (Q13, Q14)
        - Extract clean description (Q15)
        - Mark NEEDS_REVIEW if parsing fails
    """
    text = informal_task["text"]

    # Parse due date
    due_date, parsing_ok = parse_due_date(text, reference_date)
    parsed_date_keyword = None

    # Extract which keyword was parsed for description cleaning
    if due_date:
        text_lower = text.lower()
        if "today" in text_lower:
            parsed_date_keyword = "today"
        elif "tomorrow" in text_lower:
            parsed_date_keyword = "tomorrow"
        else:
            # Check for weekday names
            weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            for weekday in weekdays:
                if weekday in text_lower:
                    parsed_date_keyword = weekday
                    break

    # Parse priority
    priority = parse_priority_keywords(text)

    # Determine priority reason
    priority_reason = None
    if priority == "H":
        text_lower = text.lower()
        if "urgent" in text_lower:
            priority_reason = "detected 'urgent'"
        elif "critical" in text_lower:
            priority_reason = "detected 'critical'"
        elif "asap" in text_lower:
            priority_reason = "detected 'asap'"
    elif priority == "M":
        if "important" in text.lower():
            priority_reason = "detected 'important'"

    # Extract clean description
    clean_desc = extract_clean_description(text, parsed_date_keyword)

    # Create proposal
    proposal: TaskProposal = {
        "informal_task": informal_task,
        "proposed_description": clean_desc,
        "proposed_due": due_date,
        "proposed_priority": priority,
        "proposed_project": None,  # Future (Sprint 8+)
        "proposed_tags": [],  # Future (Sprint 8+)
        "priority_reason": priority_reason,
        "needs_review": not parsing_ok,
        "review_reason": "Could not parse date" if not parsing_ok else None,
    }

    return proposal


def create_tbd_section(proposals: List[TaskProposal]) -> str:
    """
    Generate markdown for TBD Processing section.

    Args:
        proposals: List of task proposals

    Returns:
        Formatted TBD section content

    Format per Q16:
        ```markdown
        ## TBD Processing

        - [ ] **[Y/N]** {description}
            - Proposed: `description: "{description}", due: {YYYY-MM-DD}, priority: {H|M|L}`
            - Original location: {section} (line {N})
        ```
    """
    lines = []
    lines.append("## TBD Processing")
    lines.append("")

    for proposal in proposals:
        task = proposal["informal_task"]
        desc = proposal["proposed_description"]

        # Checkbox with Y/N marker
        lines.append(f"- [ ] **[Y/N]** {desc}")

        # Proposed metadata (tab-indented per Q16)
        metadata_parts = [f'description: "{desc}"']

        if proposal["proposed_due"]:
            metadata_parts.append(f"due: {proposal['proposed_due']}")

        metadata_parts.append(f"priority: {proposal['proposed_priority']}")

        proposed_line = "\t- Proposed: `" + ", ".join(metadata_parts) + "`"
        lines.append(proposed_line)

        # Original location (1-indexed for user display, Q22)
        location = f"\t- Original location: {task['section']} (line {task['line_number'] + 1})"
        lines.append(location)

        # Priority reason if exists
        if proposal["priority_reason"]:
            lines.append(f"\t- Reason: {proposal['priority_reason']}")

        # NEEDS_REVIEW marker if needed (Q20)
        if proposal["needs_review"]:
            review_note = f"\t- *NEEDS_REVIEW: {proposal['review_reason']}*"
            lines.append(review_note)

        lines.append("")  # Blank line between proposals

    return "\n".join(lines)


def process_daily_note_step1(note_path: Path, reference_date: date) -> ProcessStepOneResult:
    """
    Step 1: Identify informal tasks, generate proposals, add TBD section.

    Args:
        note_path: Path to daily note
        reference_date: Reference date for parsing (usually today)

    Returns:
        ProcessStepOneResult with proposals and TBD section

    Workflow:
        1. Read daily note
        2. Scan for informal tasks (no UUIDs)
        3. Generate proposals for each task
        4. Create TBD Processing section
        5. Append TBD section to note (Q11)
    """
    # Read note
    content = note_path.read_text(encoding="utf-8")

    # Scan for informal tasks
    informal_tasks = scan_for_informal_tasks(content)

    # Generate proposals
    proposals: List[TaskProposal] = []
    for task in informal_tasks:
        proposal = generate_proposal(task, reference_date)
        proposals.append(proposal)

    # Create TBD section
    tbd_section = create_tbd_section(proposals)

    # Append TBD section to note (Q11: end of document)
    # First, remove existing TBD section if it exists
    if "## TBD Processing" in content:
        # Remove old TBD section
        content = re.sub(
            r"## TBD Processing\n.*?(?=\n##|\Z)",
            "",
            content,
            flags=re.DOTALL
        )

    # Append new TBD section
    updated_content = content.rstrip() + "\n\n" + tbd_section + "\n"
    note_path.write_text(updated_content, encoding="utf-8")

    # Count NEEDS_REVIEW items
    needs_review_count = sum(1 for p in proposals if p["needs_review"])

    # Return result
    result: ProcessStepOneResult = {
        "proposals_count": len(proposals),
        "needs_review_count": needs_review_count,
        "tbd_section_content": tbd_section,
    }

    return result


def parse_approvals(content: str) -> tuple[List[TaskProposal], List[TaskProposal]]:
    """
    Parse TBD Processing section for [Y] and [N] approvals.

    Args:
        content: Full note content

    Returns:
        Tuple of (approved_proposals, rejected_proposals)

    Implementation per Q17:
        - Extract proposals with [Y] or [N] markers
        - Parse user-edited metadata from Proposed line
        - Validate format, mark invalid as NEEDS_REVIEW
    """
    approved = []
    rejected = []

    # Find TBD Processing section
    tbd_match = re.search(r"## TBD Processing\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if not tbd_match:
        return (approved, rejected)

    tbd_section = tbd_match.group(1)

    # Split into proposal blocks (each starts with "- [Y/N]")
    proposal_blocks = re.split(r"\n(?=- \[.?\] \*\*\[Y/N\]\*\*)", tbd_section)

    for block in proposal_blocks:
        if not block.strip():
            continue

        # Check approval status
        approval_match = re.match(r"- \[(.?)\] \*\*\[Y/N\]\*\* (.+)", block)
        if not approval_match:
            continue

        marker = approval_match.group(1).upper()
        description_preview = approval_match.group(2)

        # Parse the Proposed line
        proposed_match = re.search(r'- Proposed: `([^`]+)`', block)
        if not proposed_match:
            continue

        proposed_line = proposed_match.group(1)

        # Extract metadata using regex (Q17)
        desc_match = re.search(r'description: "([^"]+)"', proposed_line)
        due_match = re.search(r'due: (\d{4}-\d{2}-\d{2})', proposed_line)
        priority_match = re.search(r'priority: ([HML])', proposed_line)

        if not desc_match:
            continue  # Skip malformed proposals

        description = desc_match.group(1)
        due_date = due_match.group(1) if due_match else None
        priority = priority_match.group(1) if priority_match else "L"

        # Parse original location
        location_match = re.search(r'- Original location: (.+) \(line (\d+)\)', block)
        section = location_match.group(1) if location_match else "(unknown)"
        line_num = int(location_match.group(2)) - 1 if location_match else 0  # Convert to 0-indexed

        # Check for NEEDS_REVIEW marker
        needs_review = "*NEEDS_REVIEW:" in block
        review_reason = None
        if needs_review:
            review_match = re.search(r'\*NEEDS_REVIEW: ([^*]+)\*', block)
            if review_match:
                review_reason = review_match.group(1).strip()

        # Build InformalTask (stub - we don't have original line easily)
        informal_task: InformalTask = {
            "text": description,
            "line_number": line_num,
            "section": section,
            "checkbox_state": "[ ]",
            "original_line": "",  # Will be reconstructed
        }

        # Build TaskProposal
        proposal: TaskProposal = {
            "informal_task": informal_task,
            "proposed_description": description,
            "proposed_due": due_date,
            "proposed_priority": priority,
            "proposed_project": None,
            "proposed_tags": [],
            "priority_reason": None,
            "needs_review": needs_review,
            "review_reason": review_reason,
        }

        # Categorize by marker
        if marker == "Y":
            approved.append(proposal)
        elif marker == "N":
            rejected.append(proposal)
        # Else: unmarked, skip

    return (approved, rejected)


def create_tasks_batch(proposals: List[TaskProposal], reference_date: date) -> tuple[List[TaskInfo], List[ProcessError]]:
    """
    Create TaskWarrior tasks from approved proposals.

    Args:
        proposals: List of approved proposals
        reference_date: Reference date for task creation

    Returns:
        Tuple of (created_tasks, errors)

    Implementation per Q19:
        - Call create_task() from taskwarrior integration
        - Handle checked tasks: create + mark complete
        - Collect errors, continue batch processing
    """
    from plorp.integrations.taskwarrior import create_task, mark_done, get_task_info

    created_tasks = []
    errors = []

    for proposal in proposals:
        # Skip NEEDS_REVIEW items
        if proposal["needs_review"]:
            error: ProcessError = {
                "proposal": proposal,
                "error_message": f"Needs review: {proposal['review_reason']}",
                "needs_review": True,
            }
            errors.append(error)
            continue

        try:
            # Create task in TaskWarrior
            task_uuid = create_task(
                description=proposal["proposed_description"],
                project=proposal["proposed_project"],
                due=proposal["proposed_due"],
                priority=proposal["proposed_priority"],
                tags=proposal["proposed_tags"],
            )

            if not task_uuid:
                raise Exception("create_task returned None")

            # Get full task info
            task_info = get_task_info(task_uuid)
            if not task_info:
                raise Exception(f"Could not retrieve task info for {task_uuid}")

            # Handle checked tasks (Q19)
            if proposal["informal_task"]["checkbox_state"] in ["[x]", "[X]"]:
                mark_done(task_uuid)
                task_info["status"] = "completed"

            created_tasks.append(task_info)

        except Exception as e:
            error: ProcessError = {
                "proposal": proposal,
                "error_message": str(e),
                "needs_review": True,
            }
            errors.append(error)

    return (created_tasks, errors)


def reorganize_note(
    content: str,
    created_tasks: List[TaskInfo],
    approved_proposals: List[TaskProposal],
    rejected_proposals: List[TaskProposal],
    has_errors: bool,
    reference_date: date,
) -> str:
    """
    Reorganize note after task creation.

    Args:
        content: Original note content
        created_tasks: Tasks successfully created
        approved_proposals: Approved proposals (for removal)
        rejected_proposals: Rejected proposals (keep in place)
        has_errors: Whether errors occurred
        reference_date: Reference date for TODAY/URGENT detection

    Returns:
        Updated note content

    Implementation:
        - Remove approved informal tasks from original locations (Q21)
        - Create/update ## Tasks section (Q18)
        - Create ## Created Tasks section
        - Remove/keep ## TBD Processing based on errors
    """
    lines = content.split("\n")

    # Step 1: Remove approved tasks from original locations (Q21 - string matching)
    # Build set of descriptions to remove
    approved_descriptions = {p["proposed_description"] for p in approved_proposals}

    new_lines = []
    for line in lines:
        # Check if this line is an informal task that was approved
        should_remove = False
        stripped = line.strip()

        for desc in approved_descriptions:
            # Simple substring match: if line contains "- [ ] description" or similar
            # and the description matches, remove it
            if stripped.startswith(('-', '*')) and '[' in stripped and ']' in stripped:
                # This looks like a checkbox line
                # Extract text after checkbox
                checkbox_match = re.match(r'^\s*[-*]\s*\[\s*[ xX]?\s*\]\s+(.+)$', line)
                if checkbox_match:
                    task_text = checkbox_match.group(1)
                    # If task text starts with the description (and no uuid), remove it
                    if task_text.startswith(desc) and 'uuid:' not in task_text.lower():
                        should_remove = True
                        break

        if not should_remove:
            new_lines.append(line)

    content = "\n".join(new_lines)

    # Step 2: Remove TBD Processing section if no errors
    if not has_errors:
        content = re.sub(r"\n## TBD Processing\n.*?(?=\n##|\Z)", "", content, flags=re.DOTALL)

    # Step 3: Create ## Created Tasks section
    if created_tasks:
        created_section_lines = ["\n## Created Tasks\n"]
        for task in created_tasks:
            checkbox = "[x]" if task["status"] == "completed" else "[ ]"
            task_line = f"- {checkbox} {task['description']}"

            # Add metadata
            metadata_parts = []
            if task["due"]:
                from plorp.utils.dates import format_taskwarrior_date_short
                metadata_parts.append(f"due: {format_taskwarrior_date_short(task['due'])}")
            if task["priority"]:
                metadata_parts.append(f"priority: {task['priority']}")
            metadata_parts.append(f"uuid: {task['uuid']}")

            if metadata_parts:
                task_line += " (" + ", ".join(metadata_parts) + ")"

            created_section_lines.append(task_line)

        # Insert Created Tasks section at end (before TBD if it exists, otherwise at end)
        content = content.rstrip() + "\n" + "\n".join(created_section_lines) + "\n"

    # Step 4: Update ## Tasks section for TODAY/URGENT items (Q18)
    today_urgent_tasks = [
        task for task in created_tasks
        if _is_today_or_urgent(task, reference_date)
    ]

    if today_urgent_tasks:
        # Find Tasks section
        tasks_section_match = re.search(r"(## Tasks?)\n", content, re.IGNORECASE)
        if tasks_section_match:
            # Insert tasks after ## Tasks header
            insert_pos = tasks_section_match.end()
            task_lines = []
            for task in today_urgent_tasks:
                checkbox = "[x]" if task["status"] == "completed" else "[ ]"
                task_line = f"- {checkbox} {task['description']}"

                # Add metadata
                metadata_parts = []
                if task["due"]:
                    from plorp.utils.dates import format_taskwarrior_date_short
                    metadata_parts.append(f"due: {format_taskwarrior_date_short(task['due'])}")
                if task["priority"]:
                    metadata_parts.append(f"priority: {task['priority']}")
                metadata_parts.append(f"uuid: {task['uuid']}")

                if metadata_parts:
                    task_line += " (" + ", ".join(metadata_parts) + ")"

                task_lines.append(task_line)

            # Insert at position
            content = content[:insert_pos] + "\n".join(task_lines) + "\n" + content[insert_pos:]
        else:
            # Create Tasks section (Q18)
            # Insert after front matter/title
            title_match = re.search(r"^# .+\n", content, re.MULTILINE)
            if title_match:
                insert_pos = title_match.end()
            else:
                insert_pos = 0

            tasks_header = "\n## Tasks\n"
            task_lines = []
            for task in today_urgent_tasks:
                checkbox = "[x]" if task["status"] == "completed" else "[ ]"
                task_line = f"- {checkbox} {task['description']}"

                metadata_parts = []
                if task["due"]:
                    from plorp.utils.dates import format_taskwarrior_date_short
                    metadata_parts.append(f"due: {format_taskwarrior_date_short(task['due'])}")
                if task["priority"]:
                    metadata_parts.append(f"priority: {task['priority']}")
                metadata_parts.append(f"uuid: {task['uuid']}")

                if metadata_parts:
                    task_line += " (" + ", ".join(metadata_parts) + ")"

                task_lines.append(task_line)

            tasks_section = tasks_header + "\n".join(task_lines) + "\n"
            content = content[:insert_pos] + tasks_section + content[insert_pos:]

    return content


def _is_today_or_urgent(task: TaskInfo, reference_date: date) -> bool:
    """Check if task should appear in main Tasks section."""
    # URGENT: priority is H
    if task.get("priority") == "H":
        return True

    # TODAY: due date equals reference date
    if task.get("due"):
        from plorp.utils.dates import parse_taskwarrior_date
        task_due_date = parse_taskwarrior_date(task["due"])
        if task_due_date and task_due_date == reference_date:
            return True

    return False


def process_daily_note_step2(note_path: Path, reference_date: date) -> ProcessStepTwoResult:
    """
    Step 2: Parse approvals, create tasks, reorganize note.

    Args:
        note_path: Path to daily note
        reference_date: Reference date

    Returns:
        ProcessStepTwoResult with created tasks and errors

    Workflow:
        1. Parse TBD section for [Y] and [N] markers
        2. Create TaskWarrior tasks for approved items
        3. Remove informal tasks from original locations
        4. Create ## Created Tasks section
        5. Update ## Tasks section for TODAY/URGENT items
        6. Remove TBD section if no errors, keep if NEEDS_REVIEW
    """
    # Read note
    content = note_path.read_text(encoding="utf-8")

    # Parse approvals
    approved_proposals, rejected_proposals = parse_approvals(content)

    # Create tasks from approved proposals
    created_tasks, errors = create_tasks_batch(approved_proposals, reference_date)

    # Reorganize note
    has_errors = len(errors) > 0
    updated_content = reorganize_note(
        content,
        created_tasks,
        approved_proposals,
        rejected_proposals,
        has_errors,
        reference_date
    )

    # Write updated note
    note_path.write_text(updated_content, encoding="utf-8")

    # Return result
    result: ProcessStepTwoResult = {
        "created_tasks": created_tasks,
        "approved_count": len(approved_proposals),
        "rejected_count": len(rejected_proposals),
        "errors": errors,
        "needs_review_remaining": has_errors,
    }
    return result
