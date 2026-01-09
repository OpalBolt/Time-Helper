# Specification: Nix Integration and AI System Understanding

## Overview
The primary objective of this track is to deepen the integration of Nix within the project's development and operational workflows. This will ensure that both human developers and AI systems can consistently and reproducibly build, test, and run the project's artifacts using Nix flakes. Key documentation will be updated, and the `flake.nix` will be configured to expose core tasks as easily executable Nix applications.

## Functional Requirements
1.  **Documentation Updates:**
    *   `GEMINI.md` must be updated to include a dedicated "Agent Protocols" section. This section will detail the exact Nix command strings required for building, testing, and running the project, making it explicit for AI systems.
    *   `conductor/workflow.md` must be updated to explicitly mandate the use of Nix-based commands as the standard for development and operational workflows.
    *   `README.md` must be updated to clearly communicate the "Nix-first" approach to human users, guiding them on how to use Nix for environment setup and task execution.
2.  **Nix-centric Invocation Standard:** All core project tasks, including running the application, executing tests, and performing linting/formatting, must be primarily invoked using the `nix run .#<command>` or `nix check` pattern. This ensures a consistent interface across the project.
3.  **`flake.nix` Configuration:** The `flake.nix` file must be configured to expose the following operational tasks as Nix applications or checks:
    *   The main `time-helper` application, executable via a command like `nix run .#time-helper`.
    *   The complete test suite, executable via `nix run .#tests` or `nix check`.
    *   Linting checks (e.g., `flake8`), executable via `nix run .#lint`.
    *   Formatting checks (e.g., `black`), executable via `nix run .#format`.

## Non-Functional Requirements
*   **Consistency:** The method of invoking all defined tasks must be consistent and uniform for both human developers and AI agents.
*   **Reproducibility:** All specified tasks (build, test, run, lint, format) must be fully reproducible through Nix flakes, ensuring identical environments and outcomes across different systems.
*   **Simplicity:** The Nix commands should be straightforward and easy to understand.

## Acceptance Criteria
*   `GEMINI.md` contains a clearly defined "Agent Protocols" section with comprehensive Nix command instructions for build, test, and run operations.
*   `conductor/workflow.md` explicitly outlines the standard workflow, emphasizing and mandating the use of Nix-based commands.
*   `README.md` is updated to guide human users on setting up the development environment and executing common tasks using Nix.
*   The project can be built, tested, run, linted, and formatted by executing respective `nix run .#<command>` or `nix check` commands, without direct reliance on `uv run`, `pytest`, `black`, or `flake8` commands in the primary workflow for these tasks.
*   All existing `time-helper` application functionality and tests remain operational and pass after the changes.

## Out of Scope
*   Any re-architecture or significant code changes to the core Python application logic that are not directly related to Nix integration.
*   Introduction of new features or functionalities to the `time-helper` application beyond those explicitly related to making it Nix-friendly.
