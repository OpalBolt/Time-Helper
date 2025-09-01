# Time Helper

Automated time tracking export and reporting tool for invoicing and time management.

## Overview

Time Helper is a modern CLI tool that automates the export of time tracking data and generates comprehensive weekly reports. It replaces manual processes with intelligent automation while providing beautiful, colorful output for easy copy-paste into invoicing systems.

## Features

### 🚀 Automated Week Export
- Export entire weeks with a single command
- Choose current week, previous weeks, or specific dates
- Automatic file naming and organization
- Database caching for faster subsequent operations

### 📊 Comprehensive Weekly Reports
- Daily breakdowns with tag summaries
- Weekly overview with total hours per tag
- Rich, colorful terminal output
- Invoice-ready formatting for easy copy-paste
- Annotations from time entries when available

### 💾 Database Integration
- SQLite database for caching and persistence
- Fast report generation from cached data
- Tag statistics and historical tracking
- Automatic schema initialization

### 🎨 Modern CLI Interface
- Built with Typer for intuitive commands
- Rich terminal formatting with colors and tables
- Interactive timer start (no arguments needed!)
- Comprehensive help system
- Type-safe with full Python type hints

### ⚡ Quick Timer Start

- Run `time-helper` with no arguments for instant timer start
- Simple format: `tag annotation` (space-separated)
- Example: `randcorp Developing some feature`
- Easy stop with `time-helper stop`

## Installation & Setup

This project uses Nix flakes with direnv for environment management:

```bash
# Clone the repository
git clone <repo-url>
cd time-helper

# Allow direnv to activate the environment
direnv allow

# The environment will automatically load UV and all dependencies
# Initialize the database
uv run time-helper init
```

## Usage

### Quick Start

```bash
# Start a timer interactively (no arguments needed!)
uv run time-helper
# Enter: randcorp Developing new features
# → Starts timer with tag "randcorp" and annotation "Developing new features"

# Stop the current timer
uv run time-helper stop

# Generate a report for the current week (fetches data directly from timewarrior)
uv run time-helper report

# Generate a report for last week (fetches data directly from timewarrior)
uv run time-helper report --week -1

# Generate a report for a specific date (fetches data directly from timewarrior)
uv run time-helper report --date 2025-07-28
```

**✨ Simple & Clean**: The `report` command fetches data directly from `timewarrior` using `timew export` commands and processes it in-memory. No JSON files are created or required.

**⚡ Interactive Timer**: Just run `time-helper` with no arguments for instant timer start!

### Commands

#### Timer Management

```bash
# Start timer interactively (recommended!)
uv run time-helper
# → Prompts for: "Enter tag and optional annotation (tag annotation):"
# → Example input: "randcorp Developing new features"

# Stop current timer
uv run time-helper stop
```

#### Export Time Data (Cache to Database)

```bash
# Cache current week data to database
uv run time-helper export

# Cache last week data to database
uv run time-helper export --week -1

# Cache specific week by date
uv run time-helper export --date 2025-07-28
```

#### Generate Reports

```bash
# Current week report (fetches data directly from timewarrior)
uv run time-helper report

# Last week report (fetches data directly from timewarrior)
uv run time-helper report --week -1

# Report for specific date (fetches data directly from timewarrior)
uv run time-helper report --date 2025-07-28

# Skip database cache
uv run time-helper report --no-cache
```

#### Utility Commands

```bash
# List available weeks
uv run time-helper list-weeks

# Show all known tags with statistics
uv run time-helper tags

# Initialize database schema
uv run time-helper init

# Show help for any command
uv run time-helper <command> --help
```

### Sample Output

```
Weekly Time Report - Week of July 28, 2025

Monday (2025-07-28):
  acmecorp: 5.41 hours
    Development work on web application
  admin-meeting: 0.76 hours
    Team standup and planning sessions
Daily Total: 6.17 hours

Tuesday (2025-07-29):
  techfirm: 6.30 hours
    Work on mobile app development
Daily Total: 6.30 hours

Weekly Summary:
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Tag                  ┃ Total Hours ┃ Daily Breakdown                 ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ acmecorp             │        8.63 │ Mon: 5.41, Wed: 3.22            │
│ techfirm             │        6.30 │ Tue: 6.30                       │
│ admin-meeting        │        2.27 │ Mon: 0.76, Tue: 0.51, Wed: 1.00 │
└──────────────────────┴─────────────┴─────────────────────────────────┘

Total Hours: 17.20 hours
```

## Legacy Compatibility

**Note**: All legacy file-based workflows have been removed in favor of the cleaner direct timewarrior integration. The tool now works entirely in-memory without creating intermediate files.

## Simplified Workflow

The tool has been greatly simplified. The original manual process required many commands, but now it's just one:

### Before (Manual Process)

```bash
# 7 separate export commands
timew export 2025-07-28 > work/mon.json
timew export 2025-07-29 > work/tue.json
timew export 2025-07-30 > work/wed.json
timew export 2025-07-31 > work/thu.json
timew export 2025-08-01 > work/fri.json
timew export 2025-08-02 > work/sat.json
timew export 2025-08-03 > work/sun.json

# 7 separate report commands
python main.py report work/mon.json
python main.py report work/tue.json
# ... etc
```

### After (Automated)

```bash
# Single command that does everything!
uv run time-helper report
```

**The `report` command now automatically:**

- ✅ Fetches data directly from `timewarrior` using `timew export`
- ✅ Processes data in-memory without creating files
- ✅ Generates comprehensive weekly reports
- ✅ Shows only days with actual work
- ✅ Supports database caching for faster subsequent runs

## Requirements

- Nix with flakes support
- direnv
- timewarrior (`tw` command) for exporting data
- UV (automatically installed via Nix flake)

## Project Structure

```
time_helper/
├── __init__.py
├── cli.py           # Main CLI interface
├── models.py        # Data models and types
├── database.py      # SQLite database operations
├── report_generator.py  # Report generation logic
└── week_utils.py    # Week/date utilities

test_time_helper.py  # Test script
```

## Development

The project uses modern Python practices:

- **Type Safety**: Full type hints throughout
- **Pydantic**: Data validation and parsing
- **Typer**: Modern CLI framework
- **Rich**: Beautiful terminal output
- **SQLite**: Efficient data persistence
- **UV**: Fast package management
- **Nix**: Reproducible development environment
