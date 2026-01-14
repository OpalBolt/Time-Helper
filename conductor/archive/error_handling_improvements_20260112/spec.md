# Comprehensive Error Handling Improvements

## 1. Overview
This track focuses on improving the user experience by implementing robust, application-wide error handling. Currently, errors from `timewarrior` or internal logic failures can result in unsightly Python stack traces. The goal is to intercept these errors across all commands, present them clearly to the user, and suppress raw tracebacks while preserving them in logs for debugging.

## 2. Functional Requirements

### 2.1 Custom Exception Architecture
-   **`TimewarriorError`:** Define a custom exception class to wrap `subprocess.CalledProcessError` when `timewarrior` commands fail.
-   **`TimeHelperError`:** Define a base exception class for internal application errors to ensure consistent handling.

### 2.2 Utility Layer Updates
-   **`run_timew_command` Update:** Modify this utility to catch `subprocess.CalledProcessError`, extract the error message from stderr/stdout, and raise `TimewarriorError`.

### 2.3 Command-Level Integration
-   **All Commands:** Update CLI commands (timer, report, database, etc.) to use the robust error handling mechanisms.
-   **Context-Aware Handling:** Where specific recovery or hints are possible (e.g., `start_timer` failing due to future time), catch specific exceptions to provide actionable user feedback.

### 2.4 Global Error Boundary
-   **Global Handler:** Implement a top-level exception handler (likely via `typer`'s main callback or a wrapping decorator) that acts as the final safety net.
-   **Behavior:**
    -   Catch `TimewarriorError` and `TimeHelperError`: Print the clean message in red.
    -   Catch `Exception` (unexpected): Log the full traceback to the debug log and print a generic "An unexpected error occurred" message to the user.
    -   Ensure the application exits with a non-zero status code (e.g., 1) on failure.

## 3. Non-Functional Requirements
-   **Logging:** All errors (handled and unhandled) must be logged to the application log. `DEBUG` level logs should include full tracebacks.
-   **UX:** Error messages must be concise, colored (Red for errors, Yellow for warnings/hints), and free of internal implementation details (no Python file paths) unless `--debug` is used.

## 4. Acceptance Criteria
-   Running `th start <tag> <future_time>` displays a clean error message: "Error: Time tracking cannot be set in the future."
-   No Python traceback is printed to the terminal for known or unknown errors during normal operation.
-   Tracebacks are visible only when using the `--debug` flag or checking the log file.
-   The application consistently exits with a non-zero status code on failure.
