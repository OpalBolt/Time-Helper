# Implementation Plan - Nix Integration and AI System Understanding

## Phase 1: Documentation Standards
- [x] Task: Update `GEMINI.md` with Agent Protocols [74d79dd]
    - [ ] Subtask: Add a dedicated "Agent Protocols" section
    - [ ] Subtask: Document exact Nix command strings for build, test, and run
- [x] Task: Update `conductor/workflow.md` [b07d32f]
    - [ ] Subtask: Update "Development Commands" section to mandate Nix-based commands
    - [ ] Subtask: Remove or update references to `uv run` where they conflict with the new standard
- [x] Task: Update `README.md` [15a6334]
    - [ ] Subtask: Update "Development Setup" section to reflect the Nix-first approach
    - [ ] Subtask: Update "Common Commands" section to use `nix run` patterns
- [~] Task: Conductor - User Manual Verification 'Documentation Standards' (Protocol in workflow.md)

## Phase 2: Nix Flake Implementation
- [ ] Task: Expose `time-helper` as a Nix app
    - [ ] Subtask: Edit `flake.nix` to define `apps.<system>.default` and `apps.<system>.time-helper`
    - [ ] Subtask: Verify `nix run .` and `nix run .#time-helper` execute the CLI
- [ ] Task: Expose test suite as a Nix app
    - [ ] Subtask: Edit `flake.nix` to define `apps.<system>.tests` (wrapping `pytest`)
    - [ ] Subtask: Verify `nix run .#tests` executes the test suite
- [ ] Task: Expose linting and formatting as Nix apps
    - [ ] Subtask: Edit `flake.nix` to define `apps.<system>.lint` (wrapping `flake8`)
    - [ ] Subtask: Edit `flake.nix` to define `apps.<system>.format` (wrapping `black .`)
    - [ ] Subtask: Verify `nix run .#lint` and `nix run .#format` execute successfully
- [ ] Task: Conductor - User Manual Verification 'Nix Flake Implementation' (Protocol in workflow.md)
