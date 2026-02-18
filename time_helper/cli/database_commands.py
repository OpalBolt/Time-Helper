"""Database management commands."""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List
import typer
from rich import print as rprint

from .utils import run_timew_command, handle_timew_errors
from ..database import Database
from ..models import TimeEntry
from ..logging_config import get_logger

logger = get_logger(__name__)


def _parse_entries_by_date(
    data: List[dict],
) -> tuple[Dict[str, List[TimeEntry]], int, str, str]:
    """Parse timewarrior data and group by date.

    Args:
        data: Raw timewarrior export data

    Returns:
        Tuple of (entries_by_date, total_entries, earliest_date, latest_date)
    """
    logger.debug(f"Parsing {len(data)} entries by date")

    entries_by_date = {}
    total_entries = 0
    earliest_date = None
    latest_date = None

    for entry_data in data:
        try:
            entry = TimeEntry.from_dict(entry_data)
            entry_date = entry.parse_start().date().isoformat()

            if entry_date not in entries_by_date:
                entries_by_date[entry_date] = []
            entries_by_date[entry_date].append(entry)
            total_entries += 1

            # Track date range
            if earliest_date is None or entry_date < earliest_date:
                earliest_date = entry_date
            if latest_date is None or entry_date > latest_date:
                latest_date = entry_date

        except Exception as e:
            logger.warning(f"Failed to parse entry: {e}")
            rprint(f"[yellow]Warning: Failed to parse entry: {e}[/yellow]")

    logger.debug(f"Parsed {total_entries} entries across {len(entries_by_date)} days")
    return entries_by_date, total_entries, earliest_date or "", latest_date or ""


def _get_tag_counts(entries_by_date: Dict[str, List[TimeEntry]]) -> Dict[str, int]:
    """Count occurrences of each tag.

    Args:
        entries_by_date: Dictionary mapping dates to entry lists

    Returns:
        Dictionary mapping tags to counts
    """
    tag_counts = {}

    for entries in entries_by_date.values():
        for entry in entries:
            for tag in entry.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return tag_counts


def _display_dry_run_summary(
    entries_by_date: Dict[str, List[TimeEntry]],
    total_entries: int,
    earliest_date: str,
    latest_date: str,
) -> None:
    """Display summary for dry run.

    Args:
        entries_by_date: Dictionary mapping dates to entry lists
        total_entries: Total number of entries
        earliest_date: Earliest date in data
        latest_date: Latest date in data
    """
    rprint(f"\n[bold blue]Dry Run Summary:[/bold blue]")
    rprint(f"[green]Total entries to import: {total_entries:,}[/green]")
    rprint(f"[green]Date range: {earliest_date} to {latest_date}[/green]")
    rprint(f"[green]Number of days: {len(entries_by_date)}[/green]")

    # Show tag summary
    tag_counts = _get_tag_counts(entries_by_date)
    rprint(f"[green]Unique tags: {len(tag_counts)}[/green]")

    # Show top 10 tags
    if tag_counts:
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        rprint("\n[bold blue]Top 10 tags:[/bold blue]")
        for tag, count in sorted_tags:
            rprint(f"  {tag}: {count} entries")

    rprint(
        f"\n[yellow]Use 'import-all' without --dry-run to perform the actual import.[/yellow]"
    )


@handle_timew_errors
def import_all_data(dry_run: bool = False, force: bool = False) -> None:
    """Import all time tracking data from timewarrior into the database.

    Args:
        dry_run: Show what would be imported without actually importing
        force: Force import even if database already contains data
    """
    logger.info(f"Starting import: dry_run={dry_run}, force={force}")

    db = Database()

    # Check if database already has data (unless force is used)
    if not force and not dry_run:
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM time_entries")
            existing_count = cursor.fetchone()[0]

            if existing_count > 0:
                rprint(
                    f"[yellow]Database already contains {existing_count:,} entries.[/yellow]"
                )
                rprint(
                    "[yellow]Use --force to import anyway, or --dry-run to see what would be imported.[/yellow]"
                )
                return

    action_word = "Analyzing" if dry_run else "Importing"
    rprint(
        f"[bold blue]{action_word} all timewarrior data{'...' if not dry_run else ' (dry run)...'}[/bold blue]"
    )

    # Get all data from timewarrior
    result = run_timew_command(["export", ":all"], check=True)

    # Parse JSON data
    try:
        data = json.loads(result.stdout) if result.stdout.strip() else []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        rprint(f"[red]Error parsing timewarrior data: {e}[/red]")
        raise typer.Exit(1)

    if not data:
        rprint("[yellow]No data found in timewarrior[/yellow]")
        return

    # Parse entries and group by date
    entries_by_date, total_entries, earliest_date, latest_date = _parse_entries_by_date(
        data
    )

    rprint(f"[green]Processing {len(data)} entries...[/green]")

    if dry_run:
        _display_dry_run_summary(
            entries_by_date, total_entries, earliest_date, latest_date
        )
        return

    # Store entries in database, grouped by date
    imported_count = 0
    for entry_date, entries in entries_by_date.items():
        try:
            db.store_time_entries(entries, datetime.fromisoformat(entry_date).date())
            imported_count += len(entries)
            logger.debug(f"Imported {len(entries)} entries for {entry_date}")
        except Exception as e:
            logger.error(f"Failed to import entries for {entry_date}: {e}")
            rprint(f"[red]Error importing data for {entry_date}: {e}[/red]")

    rprint(f"\n[bold green]✓ Import complete![/bold green]")
    rprint(
        f"[green]Successfully imported {imported_count:,} out of {total_entries:,} entries[/green]"
    )
    rprint(f"[green]Date range: {earliest_date} to {latest_date}[/green]")
    rprint(f"[dim]Database location: {db.db_path}[/dim]")

    logger.info(f"Import completed: {imported_count}/{total_entries} entries")


def init_database() -> None:
    """Initialize the database schema."""
    logger.info("Initializing database")

    try:
        db = Database()  # This will initialize the database
        rprint("[green]✓ Database initialized successfully![/green]")
        rprint(f"[dim]Database location: {db.db_path}[/dim]")
        logger.info(f"Database initialized at {db.db_path}")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        rprint(f"[red]Error initializing database: {e}[/red]")
        raise typer.Exit(1)


def database_status() -> None:
    """Show database status and statistics."""
    logger.debug("Checking database status")

    try:
        db = Database()

        # Get basic statistics
        with sqlite3.connect(db.db_path) as conn:
            # Total entries
            cursor = conn.execute("SELECT COUNT(*) FROM time_entries")
            total_entries = cursor.fetchone()[0]

            # Date range
            cursor = conn.execute("SELECT MIN(date), MAX(date) FROM time_entries")
            date_range = cursor.fetchone()

            # Total hours
            cursor = conn.execute("SELECT SUM(hours) FROM time_entries")
            total_hours = cursor.fetchone()[0] or 0

            # Unique tags
            cursor = conn.execute("SELECT COUNT(DISTINCT tag) FROM time_entries")
            unique_tags = cursor.fetchone()[0]

            # Recent activity (last 30 days)
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM time_entries 
                WHERE date >= date('now', '-30 days')
            """
            )
            recent_entries = cursor.fetchone()[0]

        rprint(f"[bold blue]Database Status[/bold blue]")
        rprint(f"[green]Location: {db.db_path}[/green]")
        rprint(f"[green]Total entries: {total_entries:,}[/green]")

        if total_entries > 0:
            rprint(f"[green]Date range: {date_range[0]} to {date_range[1]}[/green]")
            rprint(f"[green]Total hours tracked: {total_hours:.2f}[/green]")
            rprint(f"[green]Unique tags: {unique_tags}[/green]")
            rprint(f"[green]Recent entries (last 30 days): {recent_entries:,}[/green]")
        else:
            rprint(
                "[yellow]Database is empty. Use 'import-all' to import data from timewarrior.[/yellow]"
            )

        logger.info(
            f"Database status check: {total_entries} entries, {total_hours:.2f} hours"
        )

    except Exception as e:
        logger.error(f"Database status check failed: {e}")
        rprint(f"[red]Error checking database status: {e}[/red]")
        raise typer.Exit(1)


def show_database_path() -> None:
    """Show the path to the database file."""
    logger.debug("Showing database path")

    try:
        db = Database()
        rprint(f"[bold]Database location:[/bold] {db.db_path}")

        if db.db_path.exists():
            size = db.db_path.stat().st_size
            rprint(f"[dim]Database size: {size:,} bytes[/dim]")
        else:
            rprint(
                "[yellow]Database file does not exist yet. Run 'init' command to create it.[/yellow]"
            )

    except Exception as e:
        logger.error(f"Failed to show database path: {e}")
        rprint(f"[red]Error accessing database: {e}[/red]")
        raise typer.Exit(1)


def clear_cache(table: str = "all") -> None:
    """Clear cached data from the database.

    Args:
        table: Which table to clear ('time_entries', 'weekly_reports', or 'all')
    """
    logger.debug(f"Clearing cache for table: {table}")

    try:
        db = Database()

        if not db.db_path.exists():
            rprint("[yellow]No database file exists. Nothing to clear.[/yellow]")
            return

        with sqlite3.connect(db.db_path) as conn:
            if table == "all" or table == "time_entries":
                result = conn.execute("DELETE FROM time_entries")
                entries_deleted = result.rowcount
                rprint(
                    f"[green]✓ Cleared {entries_deleted} cached time entries[/green]"
                )

            if table == "all" or table == "weekly_reports":
                result = conn.execute("DELETE FROM weekly_reports")
                reports_deleted = result.rowcount
                rprint(
                    f"[green]✓ Cleared {reports_deleted} cached weekly reports[/green]"
                )

        # Vacuum outside of transaction to reclaim space
        with sqlite3.connect(db.db_path) as conn:
            conn.execute("VACUUM")
            rprint("[green]✓ Database optimized[/green]")

        if table == "all":
            rprint("[bold green]All cached data has been cleared![/bold green]")
        else:
            rprint(f"[bold green]Cached {table} data has been cleared![/bold green]")

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        rprint(f"[red]Error clearing cache: {e}[/red]")
        raise typer.Exit(1)


# Create typer commands
def create_database_commands() -> typer.Typer:
    """Create and return the database commands typer app."""
    db_app = typer.Typer(help="Database management commands")

    @db_app.command("import-all")
    def import_all_command(
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="Show what would be imported without actually importing",
        ),
        force: bool = typer.Option(
            False, "--force", help="Force import even if database already contains data"
        ),
    ) -> None:
        """Import all time tracking data from timewarrior into the database."""
        import_all_data(dry_run, force)

    @db_app.command("init")
    def init_command() -> None:
        """Initialize the database schema."""
        init_database()

    @db_app.command("status")
    def status_command() -> None:
        """Show database status and statistics."""
        database_status()

    @db_app.command("path")
    def path_command() -> None:
        """Show the path to the database file."""
        show_database_path()

    @db_app.command("clear-cache")
    def clear_cache_command(
        table: str = typer.Option(
            "all",
            "--table",
            help="Which table to clear: 'time_entries', 'weekly_reports', or 'all'",
        )
    ) -> None:
        """Clear cached data from the database."""
        if table not in ["all", "time_entries", "weekly_reports"]:
            rprint(
                f"[red]Error: Invalid table '{table}'. Must be 'all', 'time_entries', or 'weekly_reports'[/red]"
            )
            raise typer.Exit(1)
        clear_cache(table)

    return db_app
