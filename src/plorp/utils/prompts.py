# ABOUTME: Interactive CLI prompt utilities for user input during workflows
# ABOUTME: Provides simple prompt, choice menu, and confirmation functions with validation
"""
Interactive CLI prompts.

Utilities for getting user input during interactive workflows.
"""
from typing import List, Optional


def prompt(message: str, default: Optional[str] = None) -> str:
    """
    Prompt user for text input.

    Args:
        message: Prompt message to display
        default: Default value if user presses enter (optional)

    Returns:
        User input string, or default if provided and user pressed enter

    Example:
        >>> name = prompt("Enter your name: ")
        >>> date = prompt("Due date: ", default="tomorrow")
    """
    if default:
        message = f"{message} [{default}]: "
    else:
        message = f"{message}: "

    response = input(message).strip()

    if not response and default:
        return default

    return response


def prompt_choice(options: List[str], prompt_text: str = "Choose an option") -> int:
    """
    Prompt user to choose from a list of options.

    Args:
        options: List of option strings to display
        prompt_text: Custom prompt text (default: "Choose an option")

    Returns:
        Index of chosen option (0-based)

    Raises:
        KeyboardInterrupt: If user presses Ctrl+C (per Q1 answer)

    Example:
        >>> choice = prompt_choice(['Task', 'Note', 'Skip'])
        >>> if choice == 0:
        ...     print("Creating task")
    """
    print(f"\n{prompt_text}:")
    for i, option in enumerate(options):
        print(f"  {i + 1}. {option}")

    while True:
        try:
            response = input(f"\nEnter choice (1-{len(options)}): ").strip()
            choice_num = int(response)

            if 1 <= choice_num <= len(options):
                return choice_num - 1  # Return 0-based index

            print(f"❌ Invalid choice. Please enter 1-{len(options)}.")

        except ValueError:
            print(f"❌ Invalid input. Please enter a number 1-{len(options)}.")
        # Per Q1 answer: Let KeyboardInterrupt propagate to caller
        # except (EOFError, KeyboardInterrupt):
        #     return len(options) - 1


def confirm(message: str, default: bool = False) -> bool:
    """
    Prompt user for yes/no confirmation.

    Args:
        message: Confirmation message
        default: Default value if user presses enter

    Returns:
        True if user confirmed, False otherwise

    Example:
        >>> if confirm("Delete this task?"):
        ...     delete_task(uuid)
    """
    default_str = "Y/n" if default else "y/N"
    response = input(f"{message} [{default_str}]: ").strip().lower()

    if not response:
        return default

    return response in ("y", "yes")
