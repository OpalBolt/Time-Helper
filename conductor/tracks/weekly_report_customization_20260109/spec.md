# Enhance Weekly Report Customization and Output Options

## 1. Introduction
This specification outlines the enhancements to the `time-helper` CLI tool, focusing on improving the flexibility and utility of its weekly report generation. The goal is to provide users with more control over the report's content and presentation, as well as to support additional output formats beyond the current terminal display.

## 2. Goals
- To allow users to customize the data included in the weekly report (e.g., specific tags, date ranges).
- To enable users to select different output formats for the report (e.g., Markdown, CSV).
- To maintain the existing ease of use and efficiency of the `time-helper` CLI.

## 3. Proposed Changes

### 3.1 Command Line Interface (CLI) Enhancements
The existing `time-helper report` command will be enhanced with new options:

-   `--start-date <YYYY-MM-DD>`: Specify the start date for the report. Defaults to the beginning of the current week.
-   `--end-date <YYYY-MM-DD>`: Specify the end date for the report. Defaults to the end of the current week.
-   `--tags <tag1,tag2,...>`: Filter the report to include only entries with the specified tags.
-   `--format <format>`: Specify the output format. Supported formats: `terminal` (default), `markdown`, `csv`.

### 3.2 Report Generation Logic
The `report_generator.py` module will be updated to:
-   Accept `start_date`, `end_date`, and `tags` parameters to filter data retrieved from the SQLite database.
-   Implement logic to format the report based on the selected `--format` option.

### 3.3 Output Formats

#### 3.3.1 Terminal Output (Existing)
-   Maintain current `Rich`-based aesthetic for terminal output.

#### 3.3.2 Markdown Output
-   Generate a well-formatted Markdown table suitable for documentation or sharing.
-   Include weekly summary and daily breakdown sections as Markdown headers and lists.

#### 3.3.3 CSV Output
-   Generate a comma-separated values file suitable for import into spreadsheets.
-   Each row will represent a time entry or an aggregated summary line. The structure will be designed for easy parsing.

## 4. Acceptance Criteria
-   All new CLI options (`--start-date`, `--end-date`, `--tags`, `--format`) are functional and correctly influence report generation.
-   Markdown output is correctly formatted and readable.
-   CSV output is correctly formatted and parsable by standard spreadsheet software.
-   Reports generated with filtering options (date range, tags) accurately reflect the specified criteria.
-   No regressions are introduced to the existing terminal report functionality.
-   Documentation (CLI help messages) is updated to reflect new options.
