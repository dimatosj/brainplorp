# brainplorp Tester Guide

Thank you for testing brainplorp! This guide will get you up and running.

## Quick Start (5 minutes)

### Step 1: Install Homebrew (if needed)

If you don't have Homebrew:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install brainplorp

```bash
brew tap dimatosj/brainplorp
brew install brainplorp
```

### Step 3: Setup

```bash
brainplorp setup
```

Answer the questions - it's okay to skip optional features.

### Step 4: Test It Works

```bash
brainplorp --version
brainplorp tasks
```

## What to Test

### Core Workflows

1. **Daily Start**
   ```bash
   brainplorp start
   ```
   - Does it create a daily note?
   - Are tasks listed correctly?
   - Is the file path printed?

2. **Task Management**
   ```bash
   brainplorp tasks
   brainplorp tasks --urgent
   brainplorp tasks --project work
   ```
   - Do task queries work?
   - Is output readable and formatted nicely?
   - Do filters work correctly?

3. **Inbox Processing**
   ```bash
   brainplorp inbox add "Test inbox item"
   brainplorp inbox process
   ```
   - Does quick-add work?
   - Can you process inbox items?
   - Do created tasks appear in TaskWarrior?

4. **Configuration Validation**
   ```bash
   brainplorp config validate
   ```
   - Does it detect your vault?
   - Does it check TaskWarrior installation?
   - Are warnings/errors clear?

5. **MCP Integration** (if you use Claude Desktop)
   - Open Claude Desktop
   - Try slash commands: `/tasks`, `/urgent`, `/start`
   - Do tools work?
   - Can you create tasks via natural language?

### Installation Testing

**Things to check:**
- Did Homebrew install finish without errors?
- Did setup wizard run successfully?
- Were defaults sensible?
- Was the process confusing at any point?

### Setup Wizard Testing

**Try different scenarios:**
1. Run `brainplorp setup` with an existing Obsidian vault
2. Run `brainplorp setup` without any vault (should prompt for path)
3. Configure email inbox (optional - requires Gmail App Password)
4. Configure MCP for Claude Desktop (if you have it)

### Multi-Computer Testing (Optional)

If you have 2+ Macs:
1. Follow [MULTI_COMPUTER_SETUP.md](MULTI_COMPUTER_SETUP.md)
2. Test task sync between computers
3. Test vault sync via iCloud
4. Report any sync issues

## Bugs to Report

### High Priority
- Installation errors
- Setup wizard crashes or hangs
- Commands that don't work
- Data loss or corruption

### Medium Priority
- Confusing error messages
- Setup wizard unclear questions
- Performance issues
- Missing features you expected

### Low Priority
- Typos in documentation
- Formatting issues in output
- Feature requests
- Nice-to-have improvements

## How to Report Issues

Create a GitHub issue with:

**Title:** Short description of the problem

**Body:**
```
### What I Tried
(Steps to reproduce)

### What Happened
(Actual behavior)

### What I Expected
(Expected behavior)

### Error Messages
(Copy-paste any errors)

### Environment
- macOS version: (e.g., 14.1)
- brainplorp version: (run `brainplorp --version`)
- TaskWarrior version: (run `task --version`)
```

**Example Issue:**
```
Title: Setup wizard crashes when vault path has spaces

### What I Tried
1. Ran `brainplorp setup`
2. Entered vault path: `/Users/test/My Vault`
3. Wizard crashed

### What Happened
Error: "No such file or directory: /Users/test/My"

### What I Expected
Wizard should handle spaces in paths

### Error Messages
Traceback...

### Environment
- macOS 14.1
- brainplorp v1.6.0
- TaskWarrior 3.4.1
```

## Feedback We'd Love

Even if everything works perfectly, tell us:

- **What was confusing?** Help us improve the docs
- **What was surprising?** (good or bad)
- **What's missing?** Features you expected but didn't find
- **What delighted you?** Things that worked better than expected

## Need Help?

- **GitHub Issues:** https://github.com/dimatosj/brainplorp/issues
- **GitHub Discussions:** https://github.com/dimatosj/brainplorp/discussions
- **Documentation:** See `Docs/` folder

## Testing Checklist

Use this to track your testing progress:

- [ ] Homebrew installation
- [ ] Setup wizard (all steps)
- [ ] `brainplorp start` command
- [ ] `brainplorp tasks` command
- [ ] `brainplorp tasks` with filters (--urgent, --project, etc.)
- [ ] `brainplorp inbox add` command
- [ ] `brainplorp inbox process` workflow
- [ ] `brainplorp config validate` command
- [ ] MCP integration (if applicable)
- [ ] Multi-computer sync (if applicable)
- [ ] Documentation clarity
- [ ] Error messages clarity

## Thank You!

Your testing helps make brainplorp better for everyone. We appreciate your time and feedback!

---

**Version:** Sprint 10 (v1.6.0)
**Last Updated:** 2025-10-11
