# Time Helper

CLI tool for timewarrior automation and weekly reporting.

## What it does

Replaces manual timewarrior exports with automated weekly reports.

**Before:** 14 separate commands to export and process a week  
**After:** 1 command (`time-helper report`)

## Quick Start

```bash
# Setup (Nix + direnv)
direnv allow
uv run time-helper init

# Start timer (interactive)
time-helper
# → Enter: client-name Working on project

# Stop timer
time-helper stop

# Generate weekly report
time-helper report
```

## Core Commands

| Command | Description |
|---------|-------------|
| `time-helper` | Start timer (interactive) |
| `time-helper stop` | Stop current timer |
| `time-helper report` | Generate weekly report |
| `time-helper su :week` | Quick summary |

## Example Output

```text
Weekly Time Report - Week of July 28, 2025

Monday (2025-07-28):
  client-name: 5.41 hours
Daily Total: 5.41 hours

Weekly Summary:
┌─────────────┬─────────────┬─────────────────┐
│ Tag         │ Total Hours │ Daily Breakdown │
├─────────────┼─────────────┼─────────────────┤
│ client-name │       15.50 │ Mon: 5.41, ...  │
└─────────────┴─────────────┴─────────────────┘

Total Hours: 15.50 hours
```

## Requirements

- timewarrior (`timew`)
- Nix with flakes + direnv

## Tech Stack

Python + Typer + Rich + SQLite
