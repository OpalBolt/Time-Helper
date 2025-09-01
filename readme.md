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
# → TAB completion available for existing tags!

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
| `time-helper db-path` | Show database location |

## Database Storage

The database is stored in a central location:

- **Linux/Unix**: `~/.local/share/time-helper/time_helper.db`
- **Windows**: `%APPDATA%/time-helper/time_helper.db`

Use `time-helper db-path` to see the exact location on your system.

## Interactive Features

When starting a timer interactively with `time-helper` (no arguments), the tool provides:

- **Tab completion** for existing tags from your database
- **Case-insensitive matching** - type "adm" and TAB to complete "admin"
- **Multiple matches** - press TAB multiple times to cycle through options
- **Smart suggestions** based on your most-used tags

Example workflow:

```bash
time-helper
# Type "adm" and press TAB → completes to "admin"
# Type "admin-" and press TAB → completes to "admin-meeting"
```

### Custom Database Location

You can override the default database location by setting the `TIME_HELPER_DB_PATH` environment variable:

```bash
export TIME_HELPER_DB_PATH="/path/to/your/custom/time_helper.db"
```

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
