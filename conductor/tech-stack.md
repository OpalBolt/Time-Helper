# Technology Stack

## Core Technologies
- **Language:** Python 3.11+
- **CLI Framework:** Typer (for building intuitive command-line interfaces)
- **UI/Formatting:** Rich (for rich text, progress bars, tables, and syntax highlighting in the terminal)
- **Data Validation:** Pydantic (for data parsing and validation using Python type hints)
- **Logging:** Loguru (for flexible and powerful logging)
- **Database:** SQLite (lightweight, file-based database for local data storage)

## External Dependencies
- **Time Tracking Tool:** timewarrior (the underlying time tracking system Time-Helper integrates with)

## Development & Environment Management
- **Environment Management:** Nix (using Nix flakes for fully reproducible development, build, test, lint, and format environments and an explicit Nix-centric invocation standard for all core tasks)
 - **Environment Loader:** direnv (for automatically loading/unloading environment variables and Nix shells)
- **Python Package Manager:** uv (used primarily for dependency synchronization within the Nix development shell, but direct `uv run` commands are superseded by `nix run` for core tasks)
