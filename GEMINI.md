# Time-Helper

CLI tool for `timewarrior` automation and weekly reporting. It simplifies tracking and reporting time by providing a unified interface over `timewarrior` data, stored in a local SQLite database.

## Architecture

- **Language:** Python 3.11+
- **CLI Framework:** [Typer](https://typer.tiangolo.com/)
- **UI:** [Rich](https://rich.readthedocs.io/en/stable/)
- **Database:** SQLite (local storage)
- **Time Tracking Engine:** `timewarrior` (external dependency)
- **Package Manager:** `uv`
- **Environment:** Nix (via `flake.nix`)

### Key Directories
- `time_helper/`: Main package source.
    - `cli/`: Subcommands (`timer`, `report`, `database`, etc.) and CLI entry point logic.
    - `database.py`: Database interaction layer.
    - `report_generator.py`: Logic for generating weekly reports.
- `tests/`: Pytest test suite.

## Development Setup

The project uses **Nix** and **direnv** to manage the development environment.

1.  **Enter Environment:**
    ```bash
    direnv allow
    ```
    This will install Python, `uv`, `timewarrior`, and other dependencies defined in `flake.nix`.

2.  **Install Python Dependencies:**
    ```bash
    uv sync
    ```

## Agent Protocols

All agents working on this project must adhere to the following operational standards.

### Nix-First Execution
This project mandates the use of Nix for all build, test, and run operations to ensure reproducibility.
*   **Run Application:** `nix run .#time-helper` (or `nix run .`)
*   **Run Tests:** `nix run .#tests`
*   **Lint:** `nix run .#lint`
*   **Format:** `nix run .#format`

Do not use `uv` or direct Python commands unless explicitly debugging the Nix environment itself.

## Common Commands

### Running the Application
Use `nix run` to execute the CLI during development:

```bash
nix run .#time-helper -- [COMMAND]
```

**Examples:**
- Start timer: `nix run .#time-helper`
- Stop timer: `nix run .#time-helper -- stop`
- Generate report: `nix run .#time-helper -- report`
- Import data: `nix run .#time-helper -- db import-all`

### Testing
Run the test suite using `nix`:

```bash
nix run .#tests
```

### Formatting & Linting
The project uses `black` and `flake8` via Nix:

```bash
nix run .#format
nix run .#lint
```

## Database

The application maintains a local SQLite database to cache and organize `timewarrior` data.
- **Location:** Typically `~/.local/share/time-helper/time_helper.db` (Linux).
- **Management:** Use `nix run .#time-helper -- db status` or `db import-all` to manage data.

## Workflow

1.  **Capture:** Users track time using `time-helper` (wraps `timewarrior`).
2.  **Import:** Data is imported/synced from `timewarrior` to SQLite.
3.  **Report:** Weekly reports are generated from the SQLite database.
