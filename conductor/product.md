# Product Guide

## Initial Concept
This is a tool for myself.

## Product Definition

### Target Audience & Core Value
The primary user of **Time-Helper** is the **System Administrator / Developer** who operates primarily within the terminal environment.

**Key Problem Solved:**
Eliminates the friction of context switching and manual data wrangling associated with time tracking. It provides a fast, keyboard-centric interface for managing `timewarrior` data and generating automated reports directly from the CLI, streamlining personal productivity tracking and timesheet generation.

### Core Features
- **Unified CLI Wrapper:** A single entry point (`time-helper`) that simplifies interaction with `timewarrior`.
- **Automated Reporting:** Generates formatted weekly reports with a single command, replacing complex manual export sequences.
- **Interactive Timer:** Smart timer management with tab completion and tag suggestions based on historical data.
- **Data Import/Sync:** Seamlessly imports existing `timewarrior` data into a local SQLite database for efficient querying and reporting.
- **Nix Integration:** Fully reproducible development and runtime environment via Nix flakes.
