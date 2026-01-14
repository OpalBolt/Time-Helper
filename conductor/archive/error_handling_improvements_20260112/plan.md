# Plan: Comprehensive Error Handling Improvements

This plan outlines the steps to implement a robust, application-wide error handling system for the `time-helper` CLI, replacing raw tracebacks with user-friendly messages while maintaining debugging capabilities.

## Phase 1: Foundation and Utility Layer [checkpoint: 10a4ef8]

This phase establishes the custom exception hierarchy and updates the core execution utility to use it.

- [x] Task: Create custom exception classes in time_helper/exceptions.py. 4d05720
    - [x] Write Tests: Create `tests/test_exceptions.py` to verify exception inheritance and string representation.
    - [x] Implement Feature: Define `TimeHelperError` (base) and `TimewarriorError` (wraps subprocess errors).
- [x] Task: Refactor `run_timew_command` in `time_helper/cli/utils.py` to use `TimewarriorError`. af9a2ad
    - [x] Write Tests: Update `tests/test_basic.py` or create `tests/test_utils.py` to verify that `subprocess.CalledProcessError` is caught and raised as `TimewarriorError` with the correct message.
    - [x] Implement Feature: Modify `run_timew_command` to catch, extract stderr, and raise the custom exception.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Foundation and Utility Layer' (Protocol in workflow.md)

## Phase 2: Global Error Boundary [checkpoint: 32c9092]

This phase implements the top-level handler to catch all exceptions and format them for the user.

- [x] Task: Implement global exception handling in `time_helper/__main__.py` or `time_helper/cli/__init__.py`. da8d442
    - [x] Write Tests: Create `tests/test_error_handling.py` to simulate crashes and verify that the output is clean (no traceback) and the exit code is correct.
    - [x] Implement Feature: Wrap the `app()` call or use a Typer callback/decorator to catch `TimeHelperError` (print message) and `Exception` (log traceback + print generic message).
    - [x] Implement Feature: Ensure `--debug` flag allows tracebacks to pass through or be printed.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Global Error Boundary' (Protocol in workflow.md)

## Phase 3: Command-Specific Refinements [checkpoint: 76e3325]

This phase applies context-aware handling to specific commands to provide better hints.

- [x] Task: Update `start_timer` in `time_helper/cli/timer_commands.py` with context hints. 76e3325
    - [x] Write Tests: Add test cases to `tests/test_basic.py` (or new test file) for specific failure scenarios (e.g., future time) to verify the "hint" logic.
    - [x] Implement Feature: Catch `TimewarriorError` locally in `start_timer`, check the message content, and raise a new `TimeHelperError` with an added hint if applicable.
- [x] Task: Review and update other key commands (`report`, `db`) for consistent behavior. 76e3325
    - [x] Write Tests: Verify `report` command failure modes.
    - [x] Implement Feature: Ensure `report` commands propagate errors correctly to the global handler.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Command-Specific Refinements' (Protocol in workflow.md) 76e3325
