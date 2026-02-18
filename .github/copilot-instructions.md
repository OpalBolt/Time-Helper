# Copilot Instructions — Time-Helper

## Project Overview

CLI wrapper around `timewarrior` for automated time tracking and weekly reporting. Data flows: **timewarrior → JSON export → Pydantic models → SQLite → Rich-formatted reports** (terminal / Markdown / CSV).

## Architecture

- **`time_helper/cli/__init__.py`** — Typer app assembly. Root-level commands (`start`, `stop`, `undo`, `summary`, `annotate`) plus sub-command groups (`report`, `db`, `timer`). Default action (no subcommand) starts interactive timer.
- **`time_helper/cli/utils.py`** — Shared helpers: `run_timew_command()` wraps all `timew` subprocess calls; `parse_timew_export()` deserializes JSON to `TimeEntry`; `handle_timew_errors` decorator translates `TimewarriorError`/`CalledProcessError` into user-friendly Rich output.
- **`time_helper/models.py`** — Pydantic `TimeEntry` + dataclass report models (`TagSummary`, `DailyReport`, `WeeklyReport`). Tags are normalized to lowercase via `field_validator`. Time parsing converts UTC (`%Y%m%dT%H%M%SZ`) to local timezone.
- **`time_helper/database.py`** — `Database` class using raw `sqlite3` (no ORM). Default path follows XDG spec; overridable via `TIME_HELPER_DB_PATH` env var. Composite PK: `(id, date)`.
- **`time_helper/report_generator.py`** — `ReportGenerator` groups entries by date/tag, produces `WeeklyReport`. Separate `format_as_markdown()`/`format_as_csv()` methods for export.
- **`time_helper/exceptions.py`** — `TimeHelperError` base → `TimewarriorError`. All CLI errors funnel through `main()` in `cli/__init__.py` which catches `TimeHelperError` for clean output and re-raises unknown exceptions only in `--debug` mode.

## Build & Run (Nix-first)

All commands go through Nix flake apps — **do not use `uv run` or direct `python`**:

```bash
nix run .#time-helper -- [COMMAND]   # run the CLI
nix run .#tests                       # pytest
nix run .#lint                        # flake8
nix run .#format                      # black
```

Environment setup: `direnv allow` then `uv sync` (inside the Nix dev shell only).

## Development Workflow

When creating plans for new features or fixes, follow this workflow:

1. **Create Jira Issue** — Create a new issue in the **GRAT** project describing the work to be done. Use a clear, descriptive summary.
2. **Create Branch** — Create a new branch named after the Jira issue (e.g., `GRAT-123-feature-name` or using the issue key).
3. **Execute Plan** — Implement the changes following TDD workflow (tests first, implementation, refactor).
4. **Push Branch** — Push the new branch to GitHub remote.
5. **Create Pull Request** — Open a pull request from the feature branch to `main`, referencing the Jira issue in the description.

This workflow ensures proper tracking and integration between Jira planning and GitHub implementation.

## Testing Conventions

- Framework: **pytest** with `typer.testing.CliRunner` for CLI tests.
- Tests live in `tests/` with `test_` prefix. Naming mirrors source: `test_utils.py` → `cli/utils.py`, `test_report_generator_markdown.py` → `report_generator.py` markdown output.
- Mocking pattern: `unittest.mock.patch` on module-level imports (e.g., `patch("time_helper.cli.app")`). Database tests use temp files (`temp_db` fixture).
- **TDD workflow** is expected: write failing tests first, implement, then refactor (see `conductor/workflow.md`).

## Code Conventions

- **Style:** Google Python Style Guide (`conductor/code_styleguides/python.md`). 80-char lines, `snake_case` functions/variables, `PascalCase` classes.
- **Formatter/Linter:** `black` + `flake8` (run via `nix run .#format` / `nix run .#lint`).
- **Logging:** `loguru` via `time_helper/logging_config.py`. Use `get_logger(__name__)` — never `print()` for diagnostics. User-facing output uses `rich.print` / `Console`.
- **Error handling:** Raise `TimeHelperError` subclasses for recoverable errors. The `handle_timew_errors` decorator in `cli/utils.py` translates subprocess failures. The `main()` entrypoint catches all `TimeHelperError` exceptions.
- **Models:** Use Pydantic `BaseModel` for external data (timewarrior JSON). Use `@dataclass` for internal report structures.
- **CLI commands:** New commands go in dedicated files under `time_helper/cli/`, registered in `cli/__init__.py`. Short aliases (e.g., `su` → `summary`) are `hidden=True`.
- **Docstrings:** Required on all public functions/classes with `Args:`, `Returns:`, `Raises:` sections.

## Key Patterns

- **Subprocess interaction:** Always use `run_timew_command()` — never call `subprocess.run` directly for `timew`.
- **Tag handling:** First tag is "primary" (`get_primary_tag()`), all tags lowercase-normalized. Entries without tags become `"untagged"`.
- **Week logic:** Weeks start on Monday. `WeekUtils` handles offset calculations. Timespans use `:week-N` format converted to timewarrior syntax.
- **DB path:** Respects `TIME_HELPER_DB_PATH` env var → `XDG_DATA_HOME` → `~/.local/share/time-helper/time_helper.db`.

## Conductor Docs

The `conductor/` directory contains project management docs: `workflow.md` (TDD process, commit protocol), `product.md` / `product-guidelines.md` (UX principles), `tech-stack.md` (dependency rationale). Consult these before proposing architectural changes.
