"""Report generation and export commands."""

import json
import subprocess
from datetime import date, timedelta, datetime
from typing import List, Optional
import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from .utils import run_timew_command, handle_timew_errors, parse_timew_export
from ..database import Database
from ..models import TimeEntry
from ..report_generator import ReportGenerator
from ..week_utils import WeekUtils
from ..logging_config import get_logger

logger = get_logger(__name__)
console = Console()


def _determine_target_week(
    date_str: Optional[str], week_offset: int, year: Optional[int]
) -> date:
    """Determine the target week based on parameters.

    Args:
        date_str: Specific date string (YYYY-MM-DD)
        week_offset: Week offset from current week
        year: Year for the week

    Returns:
        Target date for the week
    """
    logger.debug(
        f"Determining target week: date_str={date_str}, offset={week_offset}, year={year}"
    )

    if date_str:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        logger.debug(f"Using specific date: {target_date}")
    else:
        week_utils = WeekUtils()
        if year is None:
            year = date.today().year
        target_date = week_utils.get_week_start_date(week_offset, year)
        logger.debug(f"Using calculated date: {target_date}")

    return target_date


def _export_day_data(day_date: date) -> List[TimeEntry]:
    """Export timewarrior data for a specific day.

    Args:
        day_date: Date to export data for

    Returns:
        List of TimeEntry objects for that day
    """
    logger.debug(f"Exporting data for {day_date}")

    date_str = day_date.strftime("%Y-%m-%d")
    result = run_timew_command(["export", date_str], check=False)

    if result.returncode != 0:
        logger.warning(f"No data found for {date_str}")
        return []

    entries = parse_timew_export(result.stdout)

    # Ensure each entry has the correct date set
    for entry in entries:
        entry.date = day_date

    return entries


def _remove_duplicate_entries(entries: List[TimeEntry]) -> List[TimeEntry]:
    """Remove duplicate entries based on ID.

    Args:
        entries: List of potentially duplicate entries

    Returns:
        List with duplicates removed
    """
    logger.debug(f"Removing duplicates from {len(entries)} entries")

    seen_ids = set()
    unique_entries = []

    for entry in entries:
        if entry.id not in seen_ids:
            unique_entries.append(entry)
            seen_ids.add(entry.id)

    logger.debug(f"Removed {len(entries) - len(unique_entries)} duplicates")
    return unique_entries


@handle_timew_errors
def export_week(
    week_offset: int = 0, year: Optional[int] = None, date_str: Optional[str] = None
) -> None:
    """Export week data for use in other tools.

    Args:
        week_offset: Week offset from current week (0=current, -1=last week, etc.)
        year: Year for the week (defaults to current year)
        date_str: Specific date within the week (YYYY-MM-DD format)
    """
    logger.info(
        f"Exporting week data: offset={week_offset}, year={year}, date={date_str}"
    )

    db = Database()
    week_utils = WeekUtils()

    # Determine the target week
    target_date = _determine_target_week(date_str, week_offset, year)

    week_start = week_utils.get_week_start(target_date)
    week_dates = week_utils.get_week_dates(week_start)

    rprint(
        f"[blue]📤 Exporting data for week of {week_start.strftime('%B %d, %Y')}...[/blue]"
    )

    all_entries: List[TimeEntry] = []

    # Export data for each day of the week
    for day_date in week_dates:
        day_entries = _export_day_data(day_date)
        all_entries.extend(day_entries)

    # Remove duplicate entries
    all_entries = _remove_duplicate_entries(all_entries)

    if not all_entries:
        rprint(
            f"[yellow]No time entries found for week of {week_start.strftime('%B %d, %Y')}[/yellow]"
        )
        return

    rprint(f"[green]✓ Exported {len(all_entries)} entries for the week[/green]")

    # Store in cache
    try:
        db.store_week_entries(week_start, all_entries)
        logger.info(f"Stored {len(all_entries)} entries in cache")
    except Exception as e:
        logger.error(f"Failed to store entries in cache: {e}")
        rprint(f"[yellow]Warning: Could not cache data: {e}[/yellow]")


@handle_timew_errors
def generate_report(
    week_offset: int = 0,
    year: Optional[int] = None,
    date_str: Optional[str] = None,
    use_cache: bool = True,
) -> None:
    """Generate a detailed report for the specified week.

    Args:
        week_offset: Week offset from current week (0=current, -1=last week, etc.)
        year: Year for the week (defaults to current year)
        date_str: Specific date within the week (YYYY-MM-DD format)
        use_cache: Use cached data from database
    """
    logger.info(
        f"Generating report: offset={week_offset}, year={year}, date={date_str}, cache={use_cache}"
    )

    db = Database()
    week_utils = WeekUtils()
    report_gen = ReportGenerator()

    # Determine the target week
    target_date = _determine_target_week(date_str, week_offset, year)

    week_start = week_utils.get_week_start(target_date)
    week_dates = week_utils.get_week_dates(week_start)

    # Try to load from cache first if enabled
    all_entries: List[TimeEntry] = []

    if use_cache:
        logger.debug("Attempting to load from cache")
        week_end = week_start + timedelta(days=6)
        cached_entries = db.get_time_entries(week_start, week_end)
        if cached_entries:
            all_entries = cached_entries
            rprint(
                f"[blue]📋 Using cached data for week of {week_start.strftime('%B %d, %Y')}...[/blue]"
            )
        else:
            logger.debug("No cached data found")

    if not all_entries:
        # Export directly from timewarrior
        rprint(
            f"[blue]📤 Exporting data directly from timewarrior for week of {week_start.strftime('%B %d, %Y')}...[/blue]"
        )

        for day_date in week_dates:
            day_entries = _export_day_data(day_date)
            all_entries.extend(day_entries)

        rprint("[green]✓ Export complete![/green]\n")

        # Remove duplicate entries
        all_entries = _remove_duplicate_entries(all_entries)

        # Store in cache by grouping entries by date
        if use_cache:
            try:
                # Group entries by date and store them
                entries_by_date = {}
                for entry in all_entries:
                    entry_date = entry.date or entry.parse_start().date()
                    if entry_date not in entries_by_date:
                        entries_by_date[entry_date] = []
                    entries_by_date[entry_date].append(entry)

                # Store each day's entries separately
                for entry_date, day_entries in entries_by_date.items():
                    db.store_time_entries(day_entries, entry_date)

                logger.info("Stored entries in cache")
            except Exception as e:
                logger.error(f"Failed to cache entries: {e}")
                rprint(f"[yellow]Warning: Could not cache data: {e}[/yellow]")

    if not all_entries:
        rprint(
            f"[yellow]No time entries found for week of {week_start.strftime('%B %d, %Y')}[/yellow]"
        )
        return

    # Generate and display the report
    weekly_report = report_gen.generate_weekly_report(all_entries, week_start)
    report_gen.print_weekly_report(weekly_report)


def list_weeks(count: int = 10) -> None:
    """List recent weeks with available data.

    Args:
        count: Number of weeks to show
    """
    logger.debug(f"Listing {count} weeks")

    week_utils = WeekUtils()
    current_date = date.today()

    table = Table(title="Available Weeks")
    table.add_column("Week Offset", style="cyan")
    table.add_column("Week Start", style="green")
    table.add_column("Week End", style="green")
    table.add_column("Description", style="yellow")

    for i in range(count):
        offset = -i
        week_start = week_utils.get_week_start_date(offset, current_date.year)
        week_end = week_start + timedelta(days=6)

        if i == 0:
            desc = "Current week"
        elif i == 1:
            desc = "Last week"
        else:
            desc = f"{i} weeks ago"

        table.add_row(
            str(offset),
            week_start.strftime("%Y-%m-%d (%a)"),
            week_end.strftime("%Y-%m-%d (%a)"),
            desc,
        )

    console.print(table)


def list_tags() -> None:
    """List all known tags from the database."""
    logger.debug("Listing tags from database")

    db = Database()
    tags = db.get_all_tags()

    if not tags:
        rprint("[yellow]No tags found in database[/yellow]")
        return

    table = Table(title="Known Tags")
    table.add_column("Tag", style="cyan")
    table.add_column("Total Hours", style="green")
    table.add_column("Last Used", style="yellow")

    for tag_info in tags:
        table.add_row(
            tag_info["tag"],
            f"{tag_info['total_hours']:.2f}",
            (
                tag_info["last_used"].strftime("%Y-%m-%d")
                if tag_info["last_used"]
                else "Never"
            ),
        )

    console.print(table)


# Create typer commands
def create_report_commands() -> typer.Typer:
    """Create and return the report commands typer app."""
    report_app = typer.Typer(help="Report generation and export commands")

    @report_app.command("export")
    def export_command(
        week_offset: int = typer.Option(
            0,
            "--week",
            "-w",
            help="Week offset from current week (0=current, -1=last week, etc.)",
        ),
        year: Optional[int] = typer.Option(
            None, "--year", "-y", help="Year for the week (defaults to current year)"
        ),
        date_str: Optional[str] = typer.Option(
            None,
            "--date",
            "-d",
            help="Specific date within the week (YYYY-MM-DD format)",
        ),
    ) -> None:
        """Export week data for use in other tools."""
        export_week(week_offset, year, date_str)

    @report_app.command("generate")
    def generate_command(
        week_offset: int = typer.Option(
            0,
            "--week",
            "-w",
            help="Week offset from current week (0=current, -1=last week, etc.)",
        ),
        year: Optional[int] = typer.Option(
            None, "--year", "-y", help="Year for the week (defaults to current year)"
        ),
        date_str: Optional[str] = typer.Option(
            None,
            "--date",
            "-d",
            help="Specific date within the week (YYYY-MM-DD format)",
        ),
        use_cache: bool = typer.Option(
            True, "--cache/--no-cache", help="Use cached data from database"
        ),
    ) -> None:
        """Generate a detailed report for the specified week."""
        generate_report(week_offset, year, date_str, use_cache)

    @report_app.command("list-weeks")
    def list_weeks_command(
        count: int = typer.Option(10, "--count", "-c", help="Number of weeks to show")
    ) -> None:
        """List recent weeks with available data."""
        list_weeks(count)

    @report_app.command("tags")
    def tags_command() -> None:
        """List all known tags from the database."""
        list_tags()

    return report_app
