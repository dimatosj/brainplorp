"""
Custom exceptions for plorp core module.

All exceptions inherit from PlorpError base class and include
structured attributes for programmatic error handling.

Exception messages are factual and technical - the CLI layer
adds user-friendly suggestions when displaying to users.
"""


class PlorpError(Exception):
    """Base exception for all plorp errors."""

    pass


class VaultNotFoundError(PlorpError):
    """Raised when Obsidian vault directory doesn't exist."""

    def __init__(self, vault_path: str):
        self.vault_path = vault_path
        super().__init__(f"Vault not found: {vault_path}")


class DailyNoteExistsError(PlorpError):
    """Raised when attempting to create a daily note that already exists."""

    def __init__(self, date: str, note_path: str):
        self.date = date
        self.note_path = note_path
        super().__init__(f"Daily note already exists: {note_path}")


class DailyNoteNotFoundError(PlorpError):
    """Raised when daily note doesn't exist for specified date."""

    def __init__(self, date: str):
        self.date = date
        super().__init__(f"Daily note not found for: {date}")


class TaskNotFoundError(PlorpError):
    """Raised when TaskWarrior task doesn't exist."""

    def __init__(self, uuid: str):
        self.uuid = uuid
        super().__init__(f"Task not found: {uuid}")


class NoteNotFoundError(PlorpError):
    """Raised when note file doesn't exist."""

    def __init__(self, note_path: str):
        self.note_path = note_path
        super().__init__(f"Note not found: {note_path}")


class NoteOutsideVaultError(PlorpError):
    """Raised when note is outside the Obsidian vault."""

    def __init__(self, note_path: str, vault_path: str):
        self.note_path = note_path
        self.vault_path = vault_path
        super().__init__(f"Note outside vault: {note_path} (vault: {vault_path})")


class InboxNotFoundError(PlorpError):
    """Raised when inbox file doesn't exist."""

    def __init__(self, inbox_path: str):
        self.inbox_path = inbox_path
        super().__init__(f"Inbox not found: {inbox_path}")


class ProjectNotFoundError(PlorpError):
    """Raised when project note doesn't exist."""

    def __init__(self, project_path: str):
        self.project_path = project_path
        super().__init__(f"Project not found: {project_path}")
