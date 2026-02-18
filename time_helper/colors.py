"""VS Code Dark+ theme colors for Rich terminal output.

This module provides color constants matching the VS Code Dark+ theme
for consistent visual presentation across the CLI application.

Reference: https://github.com/microsoft/vscode/tree/main/extensions/theme-defaults
"""

# VS Code Dark+ Theme Colors (hex values compatible with Rich)
# These colors are carefully selected to match VS Code's color scheme

# Primary colors for text emphasis
ERROR = "#f48771"  # Light red for errors
WARNING = "#dcdcaa"  # Yellow for warnings
SUCCESS = "#4ec9b0"  # Cyan/teal for success messages
INFO = "#569cd6"  # Blue for informational messages

# Secondary colors for UI elements
HIGHLIGHT = "#c586c0"  # Purple/magenta for highlights
ACCENT = "#4fc1ff"  # Light blue for accents
MUTED = "#6a9955"  # Green for muted/secondary text
DIM = "#808080"  # Gray for dimmed text

# Table and structured data colors
TABLE_HEADER = "bold #c586c0"  # Bold purple for table headers
COL_PRIMARY = "#4fc1ff"  # Light blue for primary columns
COL_TIME = "#c586c0"  # Purple for time/date columns
COL_DURATION = "#4ec9b0"  # Teal for duration columns
COL_TAG = "#569cd6"  # Blue for tag columns
COL_ANNOTATION = "#dcdcaa"  # Yellow for annotation columns

# Tag colors for consistent hash-based assignment
TAG_COLORS = [
    "#f48771",  # Red
    "#4ec9b0",  # Teal
    "#dcdcaa",  # Yellow
    "#569cd6",  # Blue
    "#c586c0",  # Magenta
    "#4fc1ff",  # Light blue
    "#ce9178",  # Orange
    "#b5cea8",  # Light green
    "#9cdcfe",  # Bright blue
    "#d7ba7d",  # Gold
    "#d16969",  # Bright red
    "#6a9955",  # Green
]
