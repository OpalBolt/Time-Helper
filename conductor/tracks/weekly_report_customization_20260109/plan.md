# Plan: Enhance Weekly Report Customization and Output Options

This plan outlines the steps to add customization and output format options to the weekly report generation in the `time-helper` CLI tool.

## Phase 1: Implement Date Range and Tag Filtering [checkpoint: 8899374]

This phase focuses on adding `--start-date`, `--end-date`, and `--tags` options to the `time-helper report` command, allowing users to filter reports by date range and specific tags.

- [x] Task: Update `time_helper/cli/report_commands.py` to add `--start-date`, `--end-date`, and `--tags` options to the `report` command. [commit: 22ae517]
    - [ ] Write Tests: Add unit tests for `report_commands.py` to verify parsing of new CLI arguments and their default values.
    - [ ] Implement Feature: Modify the `report` command function to accept these new arguments.
- [x] Task: Modify `time_helper/database.py` to allow filtering of time entries by date range and tags. [commit: 7332ad9]
    - [x] Write Tests: Add unit tests for `database.py` to verify correct filtering logic for date ranges and tags when querying time entries.
    - [x] Implement Feature: Update database query methods to incorporate `start_date`, `end_date`, and `tags` for data retrieval.
- [x] Task: Integrate filtering into `time_helper/report_generator.py`. [commit: b758baa]
    - [x] Write Tests: Add unit tests for `report_generator.py` to confirm that reports are generated correctly based on filtered data.
    - [x] Implement Feature: Pass the new filtering parameters from the CLI command to the report generation logic.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Implement Date Range and Tag Filtering' (Protocol in workflow.md)

## Phase 2: Add Markdown and CSV Output Formats

This phase focuses on extending the `time-helper report` command to support `--format markdown` and `--format csv` options.

- [x] Task: Update `time_helper/cli/report_commands.py` to add `--format` option. [commit: a6888b0]
    - [ ] Write Tests: Add unit tests for `report_commands.py` to verify parsing of the new `--format` argument.
    - [ ] Implement Feature: Modify the `report` command function to accept the `--format` argument.
- [ ] Task: Implement Markdown output in `time_helper/report_generator.py`.
    - [ ] Write Tests: Add unit tests for `report_generator.py` to verify the structure and content of Markdown output.
    - [ ] Implement Feature: Add a new function or extend existing logic to generate reports in Markdown format.
- [ ] Task: Implement CSV output in `time_helper/report_generator.py`.
    - [ ] Write Tests: Add unit tests for `report_generator.py` to verify the structure and content of CSV output.
    - [ ] Implement Feature: Add a new function or extend existing logic to generate reports in CSV format.
- [ ] Task: Update CLI help messages and documentation.
    - [ ] Write Tests: (Not applicable for documentation, but ensure CLI tests cover help output if possible.)
    - [ ] Implement Feature: Modify relevant docstrings or help text to reflect new options and formats.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Add Markdown and CSV Output Formats' (Protocol in workflow.md)
