# ABOUTME: Tests for interactive prompts - validates user input handling
# ABOUTME: Uses monkeypatch to mock input() and test various user responses
"""Tests for interactive prompts."""
import pytest
from brainplorp.utils.prompts import prompt, prompt_choice, confirm


def test_prompt_basic(monkeypatch):
    """Test basic prompt with user input."""
    monkeypatch.setattr("builtins.input", lambda _: "test response")

    result = prompt("Enter text")

    assert result == "test response"


def test_prompt_with_default_used(monkeypatch):
    """Test prompt with default when user presses enter."""
    monkeypatch.setattr("builtins.input", lambda _: "")

    result = prompt("Enter date", default="tomorrow")

    assert result == "tomorrow"


def test_prompt_with_default_overridden(monkeypatch):
    """Test prompt with default when user provides value."""
    monkeypatch.setattr("builtins.input", lambda _: "friday")

    result = prompt("Enter date", default="tomorrow")

    assert result == "friday"


def test_prompt_choice_valid(monkeypatch):
    """Test prompt_choice with valid input."""
    monkeypatch.setattr("builtins.input", lambda _: "2")

    choice = prompt_choice(["Option 1", "Option 2", "Option 3"])

    assert choice == 1  # 0-based index


def test_prompt_choice_first_option(monkeypatch):
    """Test prompt_choice selecting first option."""
    monkeypatch.setattr("builtins.input", lambda _: "1")

    choice = prompt_choice(["First", "Second"])

    assert choice == 0


def test_prompt_choice_last_option(monkeypatch):
    """Test prompt_choice selecting last option."""
    monkeypatch.setattr("builtins.input", lambda _: "3")

    choice = prompt_choice(["One", "Two", "Three"])

    assert choice == 2


def test_prompt_choice_invalid_then_valid(monkeypatch):
    """Test prompt_choice with invalid input then valid."""
    inputs = iter(["0", "5", "abc", "2"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    choice = prompt_choice(["One", "Two", "Three"])

    assert choice == 1


def test_prompt_choice_keyboard_interrupt(monkeypatch):
    """Test prompt_choice raises KeyboardInterrupt (Q1 answer)."""

    def raise_interrupt(_):
        raise KeyboardInterrupt()

    monkeypatch.setattr("builtins.input", raise_interrupt)

    # Per Q1 answer: should raise, not return last option
    with pytest.raises(KeyboardInterrupt):
        prompt_choice(["One", "Two", "Quit"])


def test_confirm_yes(monkeypatch):
    """Test confirm with 'yes' input."""
    monkeypatch.setattr("builtins.input", lambda _: "y")

    result = confirm("Proceed?")

    assert result is True


def test_confirm_no(monkeypatch):
    """Test confirm with 'no' input."""
    monkeypatch.setattr("builtins.input", lambda _: "n")

    result = confirm("Proceed?")

    assert result is False


def test_confirm_default_true(monkeypatch):
    """Test confirm with default True and empty input."""
    monkeypatch.setattr("builtins.input", lambda _: "")

    result = confirm("Proceed?", default=True)

    assert result is True


def test_confirm_default_false(monkeypatch):
    """Test confirm with default False and empty input."""
    monkeypatch.setattr("builtins.input", lambda _: "")

    result = confirm("Proceed?", default=False)

    assert result is False


def test_confirm_various_yes_forms(monkeypatch):
    """Test confirm accepts 'yes', 'Y', 'YES'."""
    for response in ["yes", "Y", "YES", "Yes"]:
        monkeypatch.setattr("builtins.input", lambda _, r=response: r)

        result = confirm("Proceed?")

        assert result is True, f"Failed for input: {response}"
