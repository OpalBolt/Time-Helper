---
name: quick_change
description: Handles small changes by creating Jira issue, branch, implementing changes, and opening PR
argument-hint: A description of the small change or fix to implement
# tools property omitted to allow all enabled tools (including MCP for Jira/GitHub)
---

# Quick Change Agent

This agent handles smaller code changes following the Time-Helper development workflow.

## Workflow

When invoked, this agent will:

1. **Create Jira Issue** — Create a new issue in the **GRAT** project with a clear, descriptive summary of the change to be made.

2. **Create Branch** — Create a new branch named after the Jira issue key (e.g., `GRAT-123-feature-name`).

3. **Implement Changes** — Make the requested code changes following TDD workflow:
   - Write failing tests first (if applicable)
   - Implement the changes
   - Ensure all tests pass
   - Run linter and formatter

4. **Push Branch** — Push the new branch to the GitHub remote repository.

5. **Create Pull Request** — Open a pull request from the feature branch to `main`, referencing the Jira issue in the description.

## Guidelines

- Follow all project conventions from `.github/copilot-instructions.md`
- Use Nix flake apps for all commands: `nix run .#tests`, `nix run .#lint`, `nix run .#format`
- Never use `uv run` or direct `python` commands
- Follow Google Python Style Guide conventions
- Use `handle_timew_errors` decorator for error handling
- Add proper docstrings with `Args:`, `Returns:`, `Raises:` sections
- All tests must pass before pushing

## When to Use

Use this agent for:
- Bug fixes
- Small feature additions
- Refactoring tasks
- Documentation updates
- Configuration changes

For larger features or architectural changes, use standard planning workflow instead.