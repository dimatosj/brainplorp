# ABOUTME: Entry point module for running plorp via "python -m plorp" command
# ABOUTME: Simply imports and invokes the CLI - enables module execution
"""
Entry point for python -m plorp
"""
from brainplorp.cli import cli

if __name__ == "__main__":
    cli()
