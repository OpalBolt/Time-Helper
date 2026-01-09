"""Shared utilities for CLI commands."""

import json
import subprocess
from datetime import datetime, timedelta, date
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from ..models import TimeEntry
from ..logging_config import get_logger

logger = get_logger(__name__)
console = Console()


def run_timew_command(
    args: List[str], check: bool = True
) -> subprocess.CompletedProcess:
    """Run a timewarrior command with proper error handling and logging.

    Args:
        args: Command arguments (without 'timew')
        check: Whether to raise CalledProcessError on non-zero exit

    Returns:
        CompletedProcess result

    Raises:
        subprocess.CalledProcessError: If command fails and check=True
        FileNotFoundError: If timewarrior is not installed
    """
    cmd = ["timew"] + args
    logger.debug(f"Running command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=check)
        logger.debug(f"Command completed with exit code: {result.returncode}")
        if result.stdout:
            logger.debug(f"Stdout: {result.stdout[:200]}...")
        if result.stderr:
            logger.debug(f"Stderr: {result.stderr}")
        return result
    except FileNotFoundError:
        logger.error("Timewarrior (timew) not found in PATH")
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e.stderr}")
        raise


def parse_timew_export(output: str) -> List[TimeEntry]:
    """Parse timewarrior export JSON into TimeEntry objects.

    Args:
        output: JSON output from timew export

    Returns:
        List of TimeEntry objects

    Raises:
        json.JSONDecodeError: If output is not valid JSON
    """
    logger.debug("Parsing timewarrior export data")

    if not output.strip():
        logger.debug("Empty output, returning empty list")
        return []

    try:
        data = json.loads(output)
        entries = [TimeEntry.from_dict(entry) for entry in data]
        logger.debug(f"Parsed {len(entries)} entries")
        return entries
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise


def convert_timespan_format(timespan: str) -> str:
    """Convert new timespan format (week-1) to timewarrior format.

    Args:
        timespan: Input timespan (e.g., ":week-1", ":week-2")

    Returns:
        Timewarrior-compatible timespan string
    """
    logger.debug(f"Converting timespan: {timespan}")

    # Handle the new format: :week-1, :week-2, etc.
    if not timespan.startswith(":") or "-" not in timespan:
        return timespan

    parts = timespan[1:].split("-")  # Remove ':' and split by '-'
    if len(parts) != 2:
        return timespan

    period, offset = parts
    if period != "week" or not offset.isdigit():
        return timespan

    # Calculate the actual date range for the week
    weeks_ago = int(offset)
    today = datetime.now()
    target_date = today - timedelta(weeks=weeks_ago)

    # Find Monday of that week (timewarrior weeks start on Monday)
    days_since_monday = target_date.weekday()  # Monday=0, Sunday=6
    monday = target_date - timedelta(days=days_since_monday)

    # Format as date range that timewarrior understands
    monday_str = monday.strftime("%Y-%m-%d")
    sunday = monday + timedelta(days=6)
    sunday_str = sunday.strftime("%Y-%m-%d")

    result = f"{monday_str} to {sunday_str}"
    logger.debug(f"Converted to: {result}")
    return result


def handle_timew_errors(func):
    """Decorator to handle common timewarrior errors.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function with error handling
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            if "No data found" in e.stderr:
                rprint("[yellow]No data found for the specified timespan[/yellow]")
            elif "There is no active time tracking" in e.stderr:
                rprint("[yellow]No active timer to stop[/yellow]")
            elif "Nothing to undo" in e.stderr:
                rprint("[yellow]Nothing to undo - no recent operations found[/yellow]")
            elif "You cannot overlap intervals" in e.stderr:
                rprint(
                    "[yellow]⚠️  Time overlap detected - the specified start time conflicts with existing intervals[/yellow]"
                )
                rprint(
                    "[dim]Hint: Use 'timew stop' to end current tracking, or choose a different start time[/dim]"
                )
            else:
                logger.error(f"Timewarrior error: {e.stderr}")
                rprint(f"[red]Error: {e.stderr}[/red]")
            raise
        except FileNotFoundError:
            rprint(
                "[red]Error: 'timew' command not found. Make sure timewarrior is installed.[/red]"
            )
            raise

    return wrapper


def get_current_entries() -> List[TimeEntry]:
    """Get current timewarrior entries for today.

    Returns:
        List of TimeEntry objects for today
    """
    logger.debug("Fetching current entries for today")

    try:
        result = run_timew_command(["export", ":day"], check=True)
        return parse_timew_export(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        logger.warning("Failed to get current entries")
        return []


def entries_have_meaningful_difference(
    before: List[TimeEntry], after: List[TimeEntry]
) -> bool:
    """Check if there's a meaningful difference between entry lists.

    Args:
        before: Entries before change
        after: Entries after change

    Returns:
        True if there's a meaningful difference (not just annotation/tag changes)
    """
    logger.debug(f"Comparing {len(before)} vs {len(after)} entries")

    # If different number of entries, that's meaningful
    if len(before) != len(after):
        logger.debug("Different number of entries - meaningful change")
        return True

    # Compare each entry for meaningful changes
    for b_entry, a_entry in zip(before, after):
        # Check for time changes (start/end times)
        if b_entry.start != a_entry.start or b_entry.end != a_entry.end:
            logger.debug("Time changes detected - meaningful change")
            return True

        # Check for ID changes (new/deleted entries)
        if b_entry.id != a_entry.id:
            logger.debug("ID changes detected - meaningful change")
            return True

    logger.debug("Only annotation or tag changes - not meaningful")
    return False


def display_entries(entries: List[TimeEntry], title: str) -> None:
    """Display a list of entries in a formatted way.

    Args:
        entries: List of TimeEntry objects
        title: Title to display above the entries
    """
    logger.debug(f"Displaying {len(entries)} entries with title: {title}")

    rprint(title)
    if not entries:
        rprint("No entries found.")
        return

    for i, entry in enumerate(entries, 1):
        start_time = entry.parse_start().strftime("%H:%M")

        if entry.end:
            end_time = entry.parse_end().strftime("%H:%M")
            duration = f"{entry.get_duration_hours():.2f}h"
        else:
            end_time = "Active"
            duration = f"{entry.get_duration_hours():.2f}h"

        annotation = entry.annotation or "No annotation"
        tags_str = f"\\[{', '.join(entry.tags)}]" if entry.tags else "\\[no tags]"
        output_line = f"  {i}. [dim]ID:{entry.id}[/dim] {start_time}-{end_time} ({duration}) {tags_str} {annotation}"
        rprint(output_line)
