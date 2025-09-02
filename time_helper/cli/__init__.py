"""Main CLI entry point for time-helper application."""

import typer
from typing import Optional

from .timer_commands import create_timer_commands, start_timer, stop_timer, undo_last_action
from .summary_commands import display_summary
from .report_commands import create_report_commands
from .database_commands import create_database_commands
from ..logging_config import setup_logging, get_logger

# Initialize logging first (silent by default)
setup_logging(verbosity=0)  # Will be overridden by callback if needed
logger = get_logger(__name__)

# Create main app
app = typer.Typer(
    help="Time tracking helper tool for timewarrior",
    pretty_exceptions_enable=False
)

# Add sub-commands
app.add_typer(create_timer_commands(), name="timer", help="Timer management")
app.add_typer(create_report_commands(), name="report", help="Report generation")
app.add_typer(create_database_commands(), name="db", help="Database management")


@app.callback(invoke_without_command=True)
def main_callback(
    verbose: int = typer.Option(0, "-v", "--verbose", count=True, help="Increase verbosity (-v for info, -vv for debug)"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging (same as -vv)"),
    ctx: typer.Context = typer.Context
) -> None:
    """Main callback to handle global options and default behavior."""
    # Determine verbosity level
    verbosity = verbose
    if debug:
        verbosity = max(verbosity, 2)  # --debug sets maximum verbosity
    
    # Reconfigure logging with the appropriate verbosity
    setup_logging(verbosity=verbosity)
    
    if verbosity >= 2:
        logger.debug("Debug logging enabled")
    elif verbosity >= 1:
        logger.info("Verbose logging enabled")
    
    # If no subcommand is invoked, start a timer interactively
    if ctx.invoked_subcommand is None:
        start_timer()


# Add individual commands at root level for convenience
@app.command("start")
def start_command(
    args: Optional[list[str]] = typer.Argument(None, help="Tag and optional annotation, with optional time (e.g., 'admin meeting 0700')")
) -> None:
    """Start a new timer with optional tags and time."""
    start_timer(args)


@app.command("stop")  
def stop_command() -> None:
    """Stop the currently active timer."""
    stop_timer()


@app.command("undo")
def undo_command() -> None:
    """Undo the last timewarrior operation and show before/after status."""
    undo_last_action()


@app.command("summary")
def summary_command(
    timespan: str = typer.Argument(":day", help="Timespan to export (e.g., :day, :week, :week-2, :month)"),
    tag_filter: Optional[str] = typer.Argument(None, help="Filter entries by tag (e.g., 'admin', 'dev')")
) -> None:
    """Display timewarrior data with formatting and optional tag filtering."""
    display_summary(timespan, tag_filter)


@app.command("su", hidden=True)
def su_command(
    timespan: str = typer.Argument(":day", help="Timespan to export (e.g., :day, :week, :week-2, :month)"),
    tag_filter: Optional[str] = typer.Argument(None, help="Filter entries by tag (e.g., 'admin', 'dev')")
) -> None:
    """Display timewarrior data with formatting and optional tag filtering (short alias).""" 
    display_summary(timespan, tag_filter)


if __name__ == "__main__":
    app()
