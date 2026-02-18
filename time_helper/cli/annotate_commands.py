"""Annotation commands for time-helper application."""

import readline
import sys
from typing import Optional
from rich.console import Console
from rich.table import Table

from ..models import TimeEntry
from .utils import run_timew_command, handle_timew_errors, parse_timew_export
from .timer_commands import undo_last_action
from ..logging_config import get_logger
from .. import colors

logger = get_logger(__name__)
console = Console()


def get_user_input(prompt: str) -> str:
    """Get user input with proper terminal handling."""
    # Only enable readline if we're in a real terminal
    if not sys.stdin.isatty():
        return input(prompt)

    try:
        # Set up basic readline for proper input handling
        readline.parse_and_bind("tab: complete")
        return input(prompt)
    except (ImportError, AttributeError):
        # Fallback if readline is not available
        return input(prompt)
    finally:
        # Clean up
        try:
            readline.set_completer(None)
        except Exception:
            pass


@handle_timew_errors
def annotate_entry(
    timespan: str = ":day",
    entry_id: Optional[int] = None,
    annotation: Optional[str] = None,
) -> None:
    """
    Update the annotation for a time entry.

    Args:
        timespan: The timespan to show entries for (e.g., :day, :week, :month)
        entry_id: The ID of the entry to annotate (if not provided, will prompt)
        annotation: The annotation text (if not provided, will prompt)
    """
    # Get entries for the specified timespan
    logger.debug(f"Fetching entries for timespan: {timespan}")
    result = run_timew_command(["export", timespan])
    entries = parse_timew_export(result.stdout)

    if not entries:
        console.print(
            f"[{colors.WARNING}]No entries found for timespan: {timespan}[/{colors.WARNING}]"
        )
        return

    # Only display current entries if we need user input (interactive mode)
    if entry_id is None:
        _display_entries_table(entries)

    # Get entry ID if not provided
    if entry_id is None:
        try:
            console.print(
                f"\n[bold {colors.ACCENT}]Available entries shown above[/bold {colors.ACCENT}]"
            )
            console.print(
                "[dim]You can enter just an ID (e.g., '2') or ID with annotation (e.g., '2 Cable management')[/dim]"
            )

            prompt_response = get_user_input(
                "Enter the ID of the entry to annotate: "
            ).strip()

            if not prompt_response:
                console.print(
                    f"[{colors.WARNING}]No input provided. Exiting.[/{colors.WARNING}]"
                )
                return

            # Try to parse "ID annotation" format (e.g., "2 Cable management")
            parts = prompt_response.split(" ", 1)
            entry_id = int(parts[0])

            # If annotation was provided along with ID, use it
            if len(parts) > 1 and annotation is None:
                annotation = parts[1]

        except ValueError:
            console.print(
                f"[{colors.ERROR}]Invalid entry ID. Please enter a number (optionally followed by annotation).[/{colors.ERROR}]"
            )
            return

    # Find the entry
    target_entry = None
    for entry in entries:
        if entry.id == entry_id:
            target_entry = entry
            break

    if target_entry is None:
        console.print(
            f"[{colors.ERROR}]Entry with ID {entry_id} not found.[/{colors.ERROR}]"
        )
        return

    # Get annotation if not provided
    if annotation is None:
        current_annotation = target_entry.annotation or "—"
        console.print(f"\n[dim]Current annotation: {current_annotation}[/dim]")

        annotation = get_user_input(
            f"Enter new annotation for entry {entry_id}: "
        ).strip()

        if not annotation:
            console.print(
                f"[{colors.WARNING}]No annotation provided. Exiting.[/{colors.WARNING}]"
            )
            return
    else:
        # When annotation is provided directly, show the former annotation
        former_annotation = target_entry.annotation or "—"
        console.print(f"[dim]Former annotation: {former_annotation}[/dim]")

    # Update the annotation using timewarrior annotate command
    # Format: timew annotate @<id> "<annotation>"
    annotate_cmd = ["annotate", f"@{entry_id}", annotation]
    run_timew_command(annotate_cmd)

    console.print(
        f"[{colors.SUCCESS}]✓ Updated annotation for entry {entry_id}: '{annotation}'[/{colors.SUCCESS}]"
    )

    # Show updated entry
    console.print("\n[bold]Updated entry:[/bold]")
    updated_result = run_timew_command(["export", timespan])
    updated_entries = parse_timew_export(updated_result.stdout)
    updated_entry = next((e for e in updated_entries if e.id == entry_id), None)
    if updated_entry:
        _display_single_entry(updated_entry)


def _display_entries_table(entries: list[TimeEntry]) -> None:
    """Display entries in a formatted table."""
    table = Table(title="Current Entries")
    table.add_column("ID", style=colors.COL_PRIMARY, no_wrap=True)
    table.add_column("Start", style=colors.COL_TIME)
    table.add_column("End", style=colors.COL_TIME)
    table.add_column("Duration", style=colors.COL_DURATION)
    table.add_column("Tags", style=colors.COL_TAG)
    table.add_column("Annotation", style=colors.COL_ANNOTATION)

    for entry in entries:
        start_time = entry.parse_start().strftime("%H:%M")

        if entry.end:
            end_time = entry.parse_end().strftime("%H:%M")
            duration = f"{entry.get_duration_hours():.2f}h"
        else:
            end_time = "Active"
            duration = f"{entry.get_duration_hours():.2f}h"

        tags = ", ".join(entry.tags) if entry.tags else "—"
        annotation = entry.annotation or "—"

        table.add_row(str(entry.id), start_time, end_time, duration, tags, annotation)

    console.print(table)


def _display_single_entry(entry: TimeEntry) -> None:
    """Display a single entry."""
    start_time = entry.parse_start().strftime("%H:%M")

    if entry.end:
        end_time = entry.parse_end().strftime("%H:%M")
        duration = f"{entry.get_duration_hours():.2f}h"
    else:
        end_time = "Active"
        duration = f"{entry.get_duration_hours():.2f}h"

    tags = ", ".join(entry.tags) if entry.tags else "—"
    annotation = entry.annotation or "—"

    console.print(f"ID: {entry.id}")
    console.print(f"Time: {start_time} - {end_time}")
    console.print(f"Duration: {duration}")
    console.print(f"Tags: {tags}")
    console.print(f"Annotation: {annotation}")


def undo_annotation() -> None:
    """Undo the last annotation change only."""
    logger.info("Undoing last annotation change")
    undo_last_action(single_operation=True)


def handle_annotate_args(args: Optional[list[str]]) -> None:
    """Parse and handle annotate command arguments intelligently."""
    if not args:
        # No arguments - interactive mode with default timespan
        annotate_entry(":day", None, None)
        return

    # Check if first argument looks like a timespan (starts with :)
    if args[0].startswith(":"):
        # Timespan mode: interactive with specified timespan
        timespan = args[0]
        annotate_entry(timespan, None, None)
    else:
        # Direct mode: entry_id and annotation
        try:
            entry_id = int(args[0])
            annotation_parts = args[1:]
            annotation = " ".join(annotation_parts) if annotation_parts else None
            annotate_entry(":day", entry_id, annotation)
        except ValueError:
            console.print(
                f"[{colors.ERROR}]Error: '{args[0]}' is not a valid entry ID or timespan[/{colors.ERROR}]"
            )
            console.print(
                "[dim]Use a number for entry ID or :day, :week, etc. for timespan[/dim]"
            )
