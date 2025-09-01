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

# Import existing timewarrior data (one-time)
time-helper import-all

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
| `time-helper import-all` | Import all timewarrior data to database |
| `time-helper db-status` | Show database statistics |
| `time-helper su :week` | Quick summary |
| `time-helper db-path` | Show database location |

## Database Storage

The database is stored in a central location:

- **Linux/Unix**: `~/.local/share/time-helper/time_helper.db`
- **Windows**: `%APPDATA%/time-helper/time_helper.db`

Use `time-helper db-path` to see the exact location on your system.

## Data Import

### Initial Setup

When setting up time-helper for the first time, you can import all your existing timewarrior data:

```bash
# Preview what would be imported
time-helper import-all --dry-run

# Import all data
time-helper import-all

# Check import results
time-helper db-status
```

### Import Options

- `--dry-run`: Preview import without making changes
- `--force`: Force import even if database contains data (may create duplicates)

The import command:

- Processes all timewarrior entries from `timew export :all`
- Groups entries by date for efficient storage
- Shows progress for large imports
- Provides detailed statistics about imported data

### Tag Normalization

All tags are automatically normalized to lowercase for consistency:

- When importing from timewarrior: `Admin` → `admin`
- When starting new timers: `MEETING` → `meeting`  
- In reports and completion: `Test-Tag` → `test-tag`

This ensures consistent tag usage across all time tracking data.

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
