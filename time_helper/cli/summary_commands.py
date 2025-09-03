"""Summary and display commands for time tracking data."""

import json
from collections import defaultdict
from typing import List, Optional
import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from .utils import run_timew_command, handle_timew_errors, convert_timespan_format, parse_timew_export
from ..models import TimeEntry
from ..logging_config import get_logger

logger = get_logger(__name__)
console = Console()


def _apply_tag_filter(entries: List[TimeEntry], tag_filter: str) -> List[TimeEntry]:
    """Filter entries by tag.
    
    Args:
        entries: List of TimeEntry objects
        tag_filter: Tag to filter by
        
    Returns:
        Filtered list of entries
    """
    logger.debug(f"Applying tag filter: {tag_filter}")
    
    filtered_entries = []
    for entry in entries:
        if any(tag_filter.lower() in tag.lower() for tag in entry.tags):
            filtered_entries.append(entry)
    
    logger.debug(f"Filtered {len(entries)} entries down to {len(filtered_entries)}")
    return filtered_entries


def _create_summary_table(entries: List[TimeEntry]) -> Table:
    """Create a summary table for time entries.
    
    Args:
        entries: List of TimeEntry objects
        
    Returns:
        Rich Table object
    """
    logger.debug(f"Creating summary table for {len(entries)} entries")
    
    # Group entries by tag and calculate totals
    tag_data = defaultdict(lambda: {"entries": [], "total_hours": 0.0})
    
    for entry in entries:
        primary_tag = entry.get_primary_tag()
        duration = entry.get_duration_hours()
        tag_data[primary_tag]["entries"].append(entry)
        tag_data[primary_tag]["total_hours"] += duration
    
    # Create summary table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Tag", style="cyan", width=20)
    table.add_column("Duration", style="green", justify="right", width=10)
    table.add_column("Entries", style="yellow", justify="right", width=8)
    table.add_column("Latest Annotation", style="white", width=40)
    
    # Sort tags by total time (descending)
    sorted_tags = sorted(tag_data.items(), key=lambda x: x[1]["total_hours"], reverse=True)
    
    for tag, data in sorted_tags:
        # Get the latest annotation for this tag
        latest_annotation = _get_latest_annotation(data["entries"])
        
        # Format duration with color coding
        hours = data["total_hours"]
        formatted_duration = _format_duration(hours)
        
        table.add_row(
            tag,
            formatted_duration,
            str(len(data["entries"])),
            latest_annotation
        )
    
    return table


def _get_latest_annotation(entries: List[TimeEntry]) -> str:
    """Get the latest annotation from a list of entries.
    
    Args:
        entries: List of TimeEntry objects
        
    Returns:
        Latest annotation or placeholder text
    """
    latest_annotation = ""
    latest_time = None
    
    for entry in entries:
        entry_time = entry.parse_start()
        if entry.annotation and (latest_time is None or entry_time > latest_time):
            latest_annotation = entry.annotation
            latest_time = entry_time
    
    return latest_annotation or "[dim]No annotation[/dim]"


def _format_duration(hours: float) -> str:
    """Format duration with color coding.
    
    Args:
        hours: Duration in hours
        
    Returns:
        Formatted duration string with color
    """
    if hours >= 4:
        return f"[bold green]{hours:.2f}h[/]"  # Long duration
    elif hours >= 2:
        return f"[yellow]{hours:.2f}h[/]"      # Medium duration  
    else:
        return f"[blue]{hours:.2f}h[/]"        # Short duration


def _create_detailed_table(entries: List[TimeEntry]) -> Table:
    """Create a detailed table for time entries.
    
    Args:
        entries: List of TimeEntry objects (should be sorted by start time)
        
    Returns:
        Rich Table object
    """
    logger.debug(f"Creating detailed table for {len(entries)} entries")
    
    detail_table = Table(show_header=True, header_style="bold magenta")
    detail_table.add_column("ID", style="dim", width=6)
    detail_table.add_column("Start", style="cyan", width=8)
    detail_table.add_column("End", style="cyan", width=8)
    detail_table.add_column("Duration", style="green", width=8)
    detail_table.add_column("Tags", style="yellow", width=15)
    detail_table.add_column("Annotation", style="white")
    
    for entry in entries:
        start_time = entry.parse_start()
        duration = entry.get_duration_hours()
        
        # Format start time
        start_str = start_time.strftime("%H:%M")
        
        # Format end time
        if entry.end:
            end_time = entry.parse_end()
            end_str = end_time.strftime("%H:%M")
        else:
            end_str = "[red]Active[/red]"
        
        # Format duration
        duration_str = _format_individual_duration(duration)
        
        # Join tags with commas
        tags_str = ", ".join(entry.tags)
        
        # Handle annotation
        annotation = entry.annotation or "[dim]—[/dim]"
        
        detail_table.add_row(str(entry.id), start_str, end_str, duration_str, tags_str, annotation)
    
    return detail_table


def _format_individual_duration(duration: float) -> str:
    """Format individual entry duration with color coding.
    
    Args:
        duration: Duration in hours
        
    Returns:
        Formatted duration string with color
    """
    if duration >= 2:
        return f"[bold green]{duration:.2f}h[/bold green]"  # Long duration
    elif duration >= 1:
        return f"[yellow]{duration:.2f}h[/yellow]"          # Medium duration
    else:
        return f"[blue]{duration:.2f}h[/blue]"              # Short duration


@handle_timew_errors
def display_summary(timespan: str, tag_filter: Optional[str] = None) -> None:
    """Display timewarrior data with formatting and optional tag filtering.
    
    Args:
        timespan: Timespan to export (e.g., ":day", ":week", ":week-2")
        tag_filter: Optional tag filter
    """
    logger.info(f"Displaying summary for timespan: {timespan}, filter: {tag_filter}")
    
    # Convert new timespan format to timewarrior format
    timew_timespan = convert_timespan_format(timespan)
    
    # Export data from timewarrior
    rprint(f"[blue]📊 Fetching time data for {timespan}...[/blue]")
    
    # Handle timespans that contain spaces (like date ranges)
    if ' ' in timew_timespan:
        cmd_args = ["export"] + timew_timespan.split()
    else:
        cmd_args = ["export", timew_timespan]
    
    result = run_timew_command(cmd_args, check=True)
    entries = parse_timew_export(result.stdout)
    
    if not entries:
        rprint(f"[yellow]No time entries found for {timespan}[/yellow]")
        return
    
    # Apply tag filter if specified
    if tag_filter:
        entries = _apply_tag_filter(entries, tag_filter)
        if not entries:
            rprint(f"[yellow]No entries found matching tag filter: {tag_filter}[/yellow]")
            return
    
    # Display the formatted summary
    _print_summary(entries, timespan, tag_filter)


def _print_summary(entries: List[TimeEntry], timespan: str, tag_filter: Optional[str] = None) -> None:
    """Print a formatted summary of time entries.
    
    Args:
        entries: List of TimeEntry objects
        timespan: Original timespan string
        tag_filter: Optional tag filter
    """
    logger.debug(f"Printing summary for {len(entries)} entries")
    
    # Calculate total hours
    total_hours = sum(entry.get_duration_hours() for entry in entries)
    
    # Create title
    title_parts = [f"Time Summary for {timespan}"]
    if tag_filter:
        title_parts.append(f"(filtered by '{tag_filter}')")
    title = " ".join(title_parts)
    
    rprint(f"\n[bold cyan]{title}[/bold cyan]")
    rprint(f"[bold white]Total: {total_hours:.2f} hours[/bold white]\n")
    
    # Show detailed entries first
    rprint("[bold cyan]Detailed Entries:[/bold cyan]")
    
    # Sort entries by start time
    sorted_entries = sorted(entries, key=lambda x: x.parse_start())
    
    # Create and display detailed table
    detail_table = _create_detailed_table(sorted_entries)
    console.print(detail_table)
    
    # Create and display summary table
    rprint("\n[bold cyan]Summary by Tags:[/bold cyan]")
    summary_table = _create_summary_table(entries)
    console.print(summary_table)


# Create typer commands
def create_summary_commands() -> typer.Typer:
    """Create and return the summary commands typer app."""
    summary_app = typer.Typer(help="Summary and display commands")
    
    @summary_app.command("summary")
    @summary_app.command("su", hidden=True)
    def summary_command(
        timespan: str = typer.Argument(":day", help="Timespan to export (e.g., :day, :week, :week-2, :month)"),
        tag_filter: Optional[str] = typer.Argument(None, help="Filter entries by tag (e.g., 'admin', 'dev')")
    ) -> None:
        """Display timewarrior data with formatting and optional tag filtering.
        
        Shows time tracking data with timezone-aware timestamps and color-coded duration indicators.
        
        COLOR CODING:
        • 🟢 Green: Long duration entries (≥4h total, ≥2h individual)
        • 🟡 Yellow: Medium duration entries (2-4h total, 1-2h individual) 
        • 🔵 Blue: Short duration entries (<2h total, <1h individual)
        • 🔵 Blue: Status and informational messages
        • ⚪ Gray/Dim: Inactive entries or missing data
        • → Red arrow: Currently active timer
        
        TIMESPAN FORMATS:
        • :day, :week, :month - Current period
        • :week-1, :week-2 - Previous periods (1 week ago, 2 weeks ago)
        • :yesterday, :today - Specific days
        
        Examples:
            time-helper su :week          # Show current week
            time-helper su :week-2        # Show 2 weeks ago
            time-helper su :week admin    # Show current week filtered by 'admin' tag
            time-helper su :day randcorp  # Show today filtered by 'randcorp' tag
        """
        display_summary(timespan, tag_filter)
    
    return summary_app
