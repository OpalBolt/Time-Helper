# Product Guidelines

## User Experience (UX) Principles

### 1. Efficiency First (Simplicity & Speed)
- **Minimal Friction:** The primary goal is to minimize the time and keystrokes required to track time and generate reports. Common actions should be accessible via short, intuitive commands or aliases.
- **Terminal-Centric Flow:** Design for users who live in the CLI. Leverage standard terminal capabilities (pipes, redirection) where appropriate, but focus on interactive ease (e.g., tab completion).
- **Clear & Concise Output:** Information should be presented clearly, using visual hierarchy (via `Rich`) to highlight key data without overwhelming the user.

### 2. Guided Power (Approachability)
- **Helpful Context:** While optimizing for speed, the tool should not be opaque. Error messages must be actionable, explaining *why* something failed and *how* to fix it.
- **Smart Defaults:** The system should work "out of the box" with sensible defaults, requiring configuration only for specific needs.
- **Discoverability:** Features like tab completion and interactive prompts should guide the user towards valid inputs (e.g., existing tags) without requiring them to memorize every option.

## Design & Style
- **Visuals:** Use the `Rich` library to provide a modern, readable CLI interface (colors, tables, progress bars) that enhances usability without being distracting.
- **Tone:** Professional, direct, and helpful. The tool is a reliable assistant, not a chatty companion.
