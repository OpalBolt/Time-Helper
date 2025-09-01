"""Time Helper CLI - Automated time tracking export and reporting tool."""

from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint
import json
from datetime import datetime, timedelta, date, timezone
import subprocess
import re
import readline
import sys
import sqlite3
from .models import TimeEntry
from .database import Database
from .report_generator import ReportGenerator
from .week_utils import WeekUtils

app = typer.Typer(
    name="time-helper",
    help="Automated time tracking export and reporting tool",
    rich_markup_mode="rich"
)

# Create subcommands for logical grouping
db_app = typer.Typer(help="Database management commands")
report_app = typer.Typer(help="Reporting and data export commands")

# Add subcommands to main app
app.add_typer(db_app, name="db")
app.add_typer(report_app, name="report")

console = Console()

class TagCompleter:
    """Tab completion for tags."""
    
    def __init__(self, tags: List[str]):
        self.tags = sorted(tags)  # Sort for consistent ordering
    
    def complete(self, text: str, state: int) -> Optional[str]:
        """Return the next possible completion for 'text'."""
        # Handle case-insensitive matching
        text_lower = text.lower()
        
        # Filter tags that start with the input text (case-insensitive)
        matches = [tag for tag in self.tags if tag.lower().startswith(text_lower)]
        
        # Return the state-th match, or None if there aren't enough matches
        try:
            return matches[state]
        except IndexError:
            return None

def get_user_input_with_completion(prompt: str, tags: List[str]) -> str:
    """Get user input with tab completion for tags."""
    # Only enable completion if we're in a real terminal
    if not sys.stdin.isatty():
        return input(prompt)
    
    try:
        # Set up tab completion
        completer = TagCompleter(tags)
        readline.set_completer(completer.complete)
        readline.parse_and_bind("tab: complete")
        
        # Get input with completion
        return input(prompt)
    except (ImportError, AttributeError):
        # Fallback if readline is not available
        return input(prompt)
    finally:
        # Clean up
        try:
            readline.set_completer(None)
        except:
            pass

def start_timer(args: Optional[List[str]] = None) -> None:
    """Start a timew timer interactively or with command line arguments."""
    try:
        # If no args provided, get input interactively
        if not args:
            rprint("[bold blue]Starting new timer...[/bold blue]")
            
            # Get available tags for completion
            try:
                db = Database()
                tag_data = db.get_all_tags()
                available_tags = [tag['tag'] for tag in tag_data]
            except Exception:
                # Fallback if database is not available
                available_tags = []
            
            # Get user input with tab completion
            prompt_text = "Enter tag and optional annotation (tag annotation): "
            user_input = get_user_input_with_completion(prompt_text, available_tags).strip()
            
            if not user_input:
                rprint("[red]Error: Tag cannot be empty[/red]")
                raise typer.Exit(1)
            
            # Parse interactive input
            parts = user_input.split(' ')
            args = parts
        
        # Check if last argument is a 4-digit time (like 0700, 1385)
        start_time = None
        if len(args) > 1 and re.match(r'^\d{4}$', args[-1]):
            start_time = args[-1]
            args = args[:-1]  # Remove time from args
        
        # First argument is the tag
        tag = args[0].lower()  # Normalize tag to lowercase
        # Rest are annotation
        annotation = " ".join(args[1:]) if len(args) > 1 else ""
        
        rprint(f"[green]Tag: {tag}[/green]")
        if annotation:
            rprint(f"[green]Annotation: {annotation}[/green]")
        if start_time:
            rprint(f"[green]Start time: {start_time}[/green]")
        
        # Build timew command
        cmd = ["timew", "start", tag]
        if start_time:
            cmd.append(start_time)
        
        # Start the timer
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Add annotation if provided
        if annotation:
            annotate_cmd = ["timew", "annotate", annotation]
            subprocess.run(annotate_cmd, capture_output=True, text=True, check=True)
        
        rprint("[bold green]✓ Timer started successfully![/bold green]")
        
    except subprocess.CalledProcessError as e:
        rprint(f"[red]Error starting timer: {e.stderr}[/red]")
        raise typer.Exit(1)
    except FileNotFoundError:
        rprint("[red]Error: 'timew' command not found. Make sure timewarrior is installed.[/red]")
        raise typer.Exit(1)
    except typer.Abort:
        rprint("[yellow]Timer start cancelled[/yellow]")
        raise typer.Exit(0)

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Main entry point - starts timer if no command is provided."""
    if ctx.invoked_subcommand is None:
        start_timer()

@app.command("start")
def start_command(
    args: Optional[List[str]] = typer.Argument(None, help="Tag and optional annotation, with optional time (e.g., 'admin meeting 0700')")
) -> None:
    """Start a timer with command line arguments."""
    start_timer(args)

@report_app.command("export")
def export_week(
    week_offset: int = typer.Option(0, "--week", "-w", help="Week offset from current week (0=current, -1=last week, etc.)"),
    year: Optional[int] = typer.Option(None, "--year", "-y", help="Year for the week (defaults to current year)"),
    date_str: Optional[str] = typer.Option(None, "--date", "-d", help="Specific date within the week (YYYY-MM-DD format)")
) -> None:
    """Export time tracking data for a week directly to database cache."""
    
    db = Database()
    week_utils = WeekUtils()
    
    # Determine the target week
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            rprint("[red]Error: Invalid date format. Use YYYY-MM-DD[/red]")
            raise typer.Exit(1)
    else:
        current_year = year or datetime.now().year
        target_date = week_utils.get_week_start_date(week_offset, current_year)
    
    week_start = week_utils.get_week_start(target_date)
    week_dates = week_utils.get_week_dates(week_start)
    
    rprint(f"[bold blue]Caching time data for week of {week_start.strftime('%B %d, %Y')}[/bold blue]")
    
    cached_entries = 0
    
    for day_date in week_dates:
        date_str_formatted = day_date.strftime("%Y-%m-%d")
        day_name = day_date.strftime("%A")
        
        try:
            rprint(f"[green]Processing {day_name} ({date_str_formatted})...[/green]")
            result = subprocess.run(
                ["timew", "export", date_str_formatted],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse and store in database
            try:
                data = json.loads(result.stdout)
                if data:
                    entries = [TimeEntry.from_dict(entry) for entry in data]
                    for entry in entries:
                        entry.date = entry.parse_start().date()
                        db.store_time_entries([entry], entry.date)
                        cached_entries += 1
                    rprint(f"[green]✓ Cached {len(entries)} entries for {day_name}[/green]")
            except json.JSONDecodeError:
                rprint(f"[yellow]Warning: Could not parse timewarrior data for {day_name}[/yellow]")
            
        except subprocess.CalledProcessError as e:
            if e.stderr and "No data found" not in e.stderr:
                rprint(f"[red]Error processing {day_name}: {e.stderr}[/red]")
        except FileNotFoundError:
            rprint("[red]Error: 'timew' command not found. Make sure timewarrior is installed.[/red]")
            raise typer.Exit(1)
    
    rprint(f"\n[bold green]Export complete![/bold green] Cached {cached_entries} entries to database.")

@report_app.command("generate")
def generate_report(
    week_offset: int = typer.Option(0, "--week", "-w", help="Week offset from current week (0=current, -1=last week, etc.)"),
    year: Optional[int] = typer.Option(None, "--year", "-y", help="Year for the week (defaults to current year)"),
    date_str: Optional[str] = typer.Option(None, "--date", "-d", help="Specific date within the week (YYYY-MM-DD format)"),
    use_cache: bool = typer.Option(True, "--cache/--no-cache", help="Use cached data from database")
) -> None:
    """Generate a comprehensive weekly report with daily breakdowns.
    
    This command exports data directly from timewarrior and processes it in-memory.
    """
    
    db = Database()
    week_utils = WeekUtils()
    report_gen = ReportGenerator()
    
    # Determine the target week
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            rprint("[red]Error: Invalid date format. Use YYYY-MM-DD[/red]")
            raise typer.Exit(1)
    else:
        current_year = year or datetime.now().year
        target_date = week_utils.get_week_start_date(week_offset, current_year)
    
    week_start = week_utils.get_week_start(target_date)
    week_dates = week_utils.get_week_dates(week_start)
    
    # Try to load from cache first if enabled
    if use_cache:
        try:
            weekly_report = db.get_weekly_report(week_start)
            if weekly_report:
                report_gen.print_weekly_report(weekly_report)
                return
        except Exception as e:
            rprint(f"[yellow]Could not load from cache: {e}[/yellow]")
    
    all_entries: List[TimeEntry] = []
    
    # Export directly from timewarrior
    rprint(f"[blue]📤 Exporting data directly from timewarrior for week of {week_start.strftime('%B %d, %Y')}...[/blue]")
    
    for day_date in week_dates:
        date_str_formatted = day_date.strftime("%Y-%m-%d")
        day_name = day_date.strftime("%A")
        
        try:
            rprint(f"[dim]  • Exporting {day_name} ({date_str_formatted})...[/dim]")
            result = subprocess.run(
                ["timew", "export", date_str_formatted],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse JSON data directly in memory
            try:
                data = json.loads(result.stdout)
                if data:  # Only process if there's actual data
                    day_entries = [TimeEntry.from_dict(entry) for entry in data]
                    for entry in day_entries:
                        # Set the date based on the actual start time, not the export date
                        entry.date = entry.parse_start().date()
                    
                    all_entries.extend(day_entries)
                    
                    # Store in database for caching (use actual start date for each entry)
                    for entry in day_entries:
                        db.store_time_entries([entry], entry.date)
                    
            except json.JSONDecodeError:
                rprint(f"[yellow]Warning: Could not parse timewarrior data for {day_name}[/yellow]")
            
        except subprocess.CalledProcessError as e:
            # Don't show error for every day - timewarrior might just have no data
            if e.stderr and "No data found" not in e.stderr:
                rprint(f"[yellow]Warning: Could not export {day_name}: {e.stderr.strip()}[/yellow]")
        except FileNotFoundError:
            rprint("[red]Error: 'timew' command not found. Make sure timewarrior is installed.[/red]")
            raise typer.Exit(1)
    
    rprint("[green]✓ Export complete![/green]\n")
    
    # Remove duplicate entries based on ID (same entry can appear in multiple day exports)
    seen_ids = set()
    unique_entries = []
    for entry in all_entries:
        if entry.id not in seen_ids:
            seen_ids.add(entry.id)
            unique_entries.append(entry)
    
    all_entries = unique_entries
    
    if not all_entries:
        rprint("[red]No time entries found for the specified week[/red]")
        rprint("[yellow]Tip: Make sure timewarrior has data for this week.[/yellow]")
        raise typer.Exit(1)
    
    # Generate and display the report
    weekly_report = report_gen.generate_weekly_report(all_entries, week_start)
    report_gen.print_weekly_report(weekly_report)
    
    # Store in cache
    if use_cache:
        try:
            db.store_weekly_report(weekly_report)
        except Exception as e:
            rprint(f"[yellow]Could not cache report: {e}[/yellow]")

@report_app.command("list-weeks")
def list_weeks(
    count: int = typer.Option(10, "--count", "-c", help="Number of weeks to show")
) -> None:
    """List recent weeks with available data."""
    
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
            desc = "Current Week"
        elif i == 1:
            desc = "Last Week"
        else:
            desc = f"{i} weeks ago"
        
        table.add_row(
            str(offset),
            week_start.strftime("%Y-%m-%d (%a)"),
            week_end.strftime("%Y-%m-%d (%a)"),
            desc
        )
    
    console.print(table)

@report_app.command("tags")
def list_tags() -> None:
    """List all known tags from the database."""
    
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
            tag_info['tag'],
            f"{tag_info['total_hours']:.2f}",
            tag_info['last_used'].strftime("%Y-%m-%d") if tag_info['last_used'] else "Never"
        )
    
    console.print(table)

@db_app.command("import-all")
def import_all_data(
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be imported without actually importing"),
    force: bool = typer.Option(False, "--force", help="Force import even if database already contains data")
) -> None:
    """Import all time tracking data from timewarrior into the database."""
    
    try:
        db = Database()
        
        # Check if database already has data (unless force is used)
        if not force and not dry_run:
            with sqlite3.connect(db.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM time_entries")
                existing_count = cursor.fetchone()[0]
                if existing_count > 0:
                    rprint(f"[yellow]Warning: Database already contains {existing_count:,} entries.[/yellow]")
                    rprint("[yellow]Use --force to import anyway (may create duplicates) or --dry-run to preview.[/yellow]")
                    confirm = typer.confirm("Continue with import?")
                    if not confirm:
                        rprint("[yellow]Import cancelled[/yellow]")
                        return
        
        action_word = "Analyzing" if dry_run else "Importing"
        rprint(f"[bold blue]{action_word} all timewarrior data{'...' if not dry_run else ' (dry run)...'}[/bold blue]")
        
        # Get all data from timewarrior
        result = subprocess.run(
            ["timew", "export", ":all"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse JSON data
        try:
            data = json.loads(result.stdout)
            if not data:
                rprint("[yellow]No data found in timewarrior[/yellow]")
                return
                
        except json.JSONDecodeError as e:
            rprint(f"[red]Error parsing timewarrior data: {e}[/red]")
            raise typer.Exit(1)
        
        # Convert to TimeEntry objects and group by date
        entries_by_date = {}
        total_entries = 0
        earliest_date = None
        latest_date = None
        
        rprint(f"[green]Processing {len(data)} entries...[/green]")
        
        for entry_data in data:
            try:
                entry = TimeEntry.from_dict(entry_data)
                # Set the date based on the start time
                entry.date = entry.parse_start().date()
                
                # Track date range
                if earliest_date is None or entry.date < earliest_date:
                    earliest_date = entry.date
                if latest_date is None or entry.date > latest_date:
                    latest_date = entry.date
                
                # Group entries by date for efficient database storage
                if entry.date not in entries_by_date:
                    entries_by_date[entry.date] = []
                entries_by_date[entry.date].append(entry)
                total_entries += 1
                
            except Exception as e:
                rprint(f"[yellow]Warning: Could not process entry {entry_data.get('id', 'unknown')}: {e}[/yellow]")
                continue
        
        if dry_run:
            # Show summary for dry run
            rprint(f"\n[bold blue]Dry Run Summary:[/bold blue]")
            rprint(f"[green]Total entries to import: {total_entries:,}[/green]")
            rprint(f"[green]Date range: {earliest_date} to {latest_date}[/green]")
            rprint(f"[green]Number of days: {len(entries_by_date)}[/green]")
            
            # Show tag summary
            tag_counts = {}
            for entries in entries_by_date.values():
                for entry in entries:
                    tag = entry.get_primary_tag()
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            rprint(f"[green]Unique tags: {len(tag_counts)}[/green]")
            
            # Show top 10 tags
            if tag_counts:
                sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                rprint(f"\n[bold blue]Top 10 tags by entry count:[/bold blue]")
                for tag, count in sorted_tags:
                    rprint(f"[dim]  • {tag}: {count} entries[/dim]")
            
            rprint(f"\n[yellow]Use 'import-all' without --dry-run to perform the actual import.[/yellow]")
            return
        
        # Store entries in database, grouped by date
        imported_count = 0
        for entry_date, entries in entries_by_date.items():
            try:
                db.store_time_entries(entries, entry_date)
                imported_count += len(entries)
                if len(entries_by_date) > 20:  # Only show progress for large imports
                    rprint(f"[dim]  • Imported {len(entries)} entries for {entry_date}[/dim]")
            except Exception as e:
                rprint(f"[yellow]Warning: Could not store entries for {entry_date}: {e}[/yellow]")
        
        rprint(f"\n[bold green]✓ Import complete![/bold green]")
        rprint(f"[green]Successfully imported {imported_count:,} out of {total_entries:,} entries[/green]")
        rprint(f"[green]Date range: {earliest_date} to {latest_date}[/green]")
        rprint(f"[dim]Database location: {db.db_path}[/dim]")
        
    except subprocess.CalledProcessError as e:
        rprint(f"[red]Error running timewarrior export: {e.stderr}[/red]")
        raise typer.Exit(1)
    except FileNotFoundError:
        rprint("[red]Error: 'timew' command not found. Make sure timewarrior is installed.[/red]")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Unexpected error during import: {e}[/red]")
        raise typer.Exit(1)

@db_app.command("init")
def init_database() -> None:
    """Initialize the database schema."""
    
    try:
        db = Database()  # This will initialize the database
        rprint("[green]✓ Database initialized successfully![/green]")
        rprint(f"[dim]Database location: {db.db_path}[/dim]")
    except Exception as e:
        rprint(f"[red]Error initializing database: {e}[/red]")
        raise typer.Exit(1)

@db_app.command("status")
def database_status() -> None:
    """Show database status and statistics."""
    
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
            cursor = conn.execute("""
                SELECT COUNT(*) FROM time_entries 
                WHERE date >= date('now', '-30 days')
            """)
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
            rprint("[yellow]Database is empty. Use 'import-all' to import data from timewarrior.[/yellow]")
            
    except Exception as e:
        rprint(f"[red]Error checking database status: {e}[/red]")
        raise typer.Exit(1)

@db_app.command("path")
def show_database_path() -> None:
    """Show the path to the database file."""
    
    try:
        db = Database()
        rprint(f"[bold]Database location:[/bold] {db.db_path}")
        if db.db_path.exists():
            size = db.db_path.stat().st_size
            rprint(f"[dim]Database size: {size:,} bytes[/dim]")
        else:
            rprint("[yellow]Database file does not exist yet. Run 'init' command to create it.[/yellow]")
    except Exception as e:
        rprint(f"[red]Error accessing database: {e}[/red]")
        raise typer.Exit(1)


def _convert_timespan_format(timespan: str) -> str:
    """Convert new timespan format (week-1) to timewarrior format."""
    # Handle the new format: :week-1, :week-2, etc.
    if timespan.startswith(':') and '-' in timespan:
        parts = timespan[1:].split('-')  # Remove ':' and split by '-'
        if len(parts) == 2:
            period, offset = parts
            if period == 'week' and offset.isdigit():
                # Calculate the actual date range for the week
                from datetime import datetime, timedelta
                
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
                
                return f"{monday_str} to {sunday_str}"
    
    # Return as-is for other formats
    return timespan


def _display_summary(timespan: str, tag_filter: Optional[str]) -> None:
    try:
        # Convert new timespan format to timewarrior format
        timew_timespan = _convert_timespan_format(timespan)
        
        # Export data from timewarrior
        rprint(f"[blue]📊 Fetching time data for {timespan}...[/blue]")
        
        # Handle timespans that contain spaces (like date ranges)
        if ' ' in timew_timespan:
            cmd_args = ["timew", "export"] + timew_timespan.split()
        else:
            cmd_args = ["timew", "export", timew_timespan]
        
        result = subprocess.run(
            cmd_args,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse JSON data
        try:
            data = json.loads(result.stdout)
            if not data:
                rprint(f"[yellow]No time entries found for {timespan}[/yellow]")
                return
                
        except json.JSONDecodeError:
            rprint("[red]Error: Could not parse timewarrior data[/red]")
            raise typer.Exit(1)
        
        # Convert to TimeEntry objects
        entries = [TimeEntry.from_dict(entry) for entry in data]
        
        # Apply tag filter if specified
        if tag_filter:
            filtered_entries = []
            for entry in entries:
                if any(tag_filter.lower() in tag.lower() for tag in entry.tags):
                    filtered_entries.append(entry)
            entries = filtered_entries
            
            if not entries:
                rprint(f"[yellow]No entries found matching tag filter: {tag_filter}[/yellow]")
                return
        
        # Display the formatted summary
        _print_summary(entries, timespan, tag_filter)
        
    except subprocess.CalledProcessError as e:
        if "No data found" in e.stderr:
            rprint(f"[yellow]No data found for {timespan}[/yellow]")
        else:
            rprint(f"[red]Error fetching data: {e.stderr}[/red]")
            raise typer.Exit(1)
    except FileNotFoundError:
        rprint("[red]Error: 'timew' command not found. Make sure timewarrior is installed.[/red]")
        raise typer.Exit(1)


def _print_summary(entries: List[TimeEntry], timespan: str, tag_filter: Optional[str] = None) -> None:
    """Print a formatted summary of time entries with colors and timezone support."""
    from collections import defaultdict
    
    # Group entries by tag and calculate totals
    tag_data = defaultdict(lambda: {"entries": [], "total_hours": 0.0})
    total_hours = 0.0
    
    for entry in entries:
        primary_tag = entry.get_primary_tag()
        duration = entry.get_duration_hours()
        tag_data[primary_tag]["entries"].append(entry)
        tag_data[primary_tag]["total_hours"] += duration
        total_hours += duration
    
    # Create title
    title_parts = [f"Time Summary for {timespan}"]
    if tag_filter:
        title_parts.append(f"(filtered by '{tag_filter}')")
    title = " ".join(title_parts)
    
    rprint(f"\n[bold cyan]{title}[/bold cyan]")
    rprint(f"[bold white]Total: {total_hours:.2f} hours[/bold white]\n")
    
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
        latest_annotation = ""
        latest_time = None
        
        for entry in data["entries"]:
            entry_time = entry.parse_start()
            if entry.annotation and (latest_time is None or entry_time > latest_time):
                latest_annotation = entry.annotation
                latest_time = entry_time
        
        if not latest_annotation:
            latest_annotation = "[dim]No annotation[/dim]"
        
        # Neutral color coding for duration (no judgment about productivity)
        hours = data["total_hours"]
        if hours >= 4:
            duration_style = "[bold green]"  # Long duration
        elif hours >= 2:
            duration_style = "[yellow]"      # Medium duration  
        else:
            duration_style = "[blue]"        # Short duration
        
        formatted_duration = f"{duration_style}{hours:.2f}h[/]"
        
        table.add_row(
            tag,
            formatted_duration,
            str(len(data["entries"])),
            latest_annotation
        )
    
    console.print(table)
    
    # Show detailed entries if there are few enough
    if len(entries) <= 15:
        rprint("\n[bold cyan]Detailed Entries:[/bold cyan]")
        
        # Sort entries by start time
        sorted_entries = sorted(entries, key=lambda x: x.parse_start())
        
        detail_table = Table(show_header=True, header_style="bold magenta")
        detail_table.add_column("Start", style="cyan", width=8)
        detail_table.add_column("End", style="cyan", width=8)
        detail_table.add_column("Duration", style="green", width=8)
        detail_table.add_column("Tags", style="yellow", width=15)
        detail_table.add_column("Annotation", style="white")
        
        for entry in sorted_entries:
            start_time = entry.parse_start()
            duration = entry.get_duration_hours()
            
            # Format start time with timezone
            start_str = start_time.strftime("%H:%M")
            
            # Format end time
            if entry.end:
                end_time = entry.parse_end()
                end_str = end_time.strftime("%H:%M")
            else:
                end_str = "[red]Active[/red]"
            
            # Neutral color coding for individual entries (no productivity judgment)
            if duration >= 2:
                duration_str = f"[bold green]{duration:.2f}h[/bold green]"  # Long duration
            elif duration >= 1:
                duration_str = f"[yellow]{duration:.2f}h[/yellow]"          # Medium duration
            else:
                duration_str = f"[blue]{duration:.2f}h[/blue]"              # Short duration
            
            # Join tags with commas
            tags_str = ", ".join(entry.tags)
            
            # Handle annotation
            annotation = entry.annotation or "[dim]—[/dim]"
            
            detail_table.add_row(start_str, end_str, duration_str, tags_str, annotation)
        
        console.print(detail_table)


@app.command("stop")
def stop_timer() -> None:
    """Stop the currently active timer."""
    try:
        result = subprocess.run(
            ["timew", "stop"],
            capture_output=True,
            text=True,
            check=True
        )
        rprint("[bold green]✓ Timer stopped successfully![/bold green]")
        
        # Show what was stopped if there's output
        if result.stdout.strip():
            rprint(f"[dim]{result.stdout.strip()}[/dim]")
            
    except subprocess.CalledProcessError as e:
        if "There is no active time tracking" in e.stderr:
            rprint("[yellow]No active timer to stop[/yellow]")
        else:
            rprint(f"[red]Error stopping timer: {e.stderr}[/red]")
            raise typer.Exit(1)
    except FileNotFoundError:
        rprint("[red]Error: 'timew' command not found. Make sure timewarrior is installed.[/red]")
        raise typer.Exit(1)


def _get_current_entries() -> List[TimeEntry]:
    """Get current timewarrior entries for today."""
    try:
        result = subprocess.run(
            ["timew", "export", ":day"],
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.stdout.strip():
            data = json.loads(result.stdout)
            return [TimeEntry.from_dict(entry) for entry in data]
        return []
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return []


def _entries_have_meaningful_difference(before: List[TimeEntry], after: List[TimeEntry]) -> bool:
    """Check if there's a meaningful difference between entry lists (not just annotation/tag changes)."""
    # If different number of entries, that's meaningful
    if len(before) != len(after):
        return True
    
    # Compare each entry for meaningful changes
    for b_entry, a_entry in zip(before, after):
        # Check for time changes (start/end times)
        if b_entry.start != a_entry.start or b_entry.end != a_entry.end:
            return True
        
        # Check for ID changes (new/deleted entries)
        if b_entry.id != a_entry.id:
            return True
    
    # Only annotation or tag changes - not meaningful
    return False


def _display_entries(entries: List[TimeEntry], title: str) -> None:
    """Display a list of entries in a formatted way."""
    rprint(title)
    if not entries:
        rprint("No entries found.")
        return
        
    for i, entry in enumerate(entries[-3:], 1):
        start_time = entry.parse_start().strftime("%H:%M")
        if entry.end:
            end_time = entry.parse_end().strftime("%H:%M")
            duration = f"{entry.get_duration_hours():.2f}h"
        else:
            end_time = "Active"
            duration = f"{entry.get_duration_hours():.2f}h"
        
        annotation = entry.annotation or "No annotation"
        tags_str = f"\\[{', '.join(entry.tags)}]" if entry.tags else "\\[no tags]"
        output_line = f"  {i}. {start_time}-{end_time} ({duration}) {tags_str} {annotation}"
        rprint(output_line)


@app.command("summary")
@app.command("su", hidden=True)
def su(
    timespan: str = typer.Argument(":day", help="Timespan to export (e.g., :day, :week, :week-2, :month)"),
    tag_filter: Optional[str] = typer.Argument(None, help="Filter entries by tag (e.g., 'admin', 'dev')")
) -> None:
    """Display timewarrior data with formatting and optional tag filtering (short alias for summary).
    
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
    _display_summary(timespan, tag_filter)

@app.command("undo")
def undo_last_action() -> None:
    """Undo the last timewarrior operation and show before/after status. 
    
    If the undo only removes tags or annotations, it will repeat the undo 
    until there's a meaningful state change (time changes, entry additions/deletions).
    """
    try:
        # Get initial state
        initial_entries = _get_current_entries()
        _display_entries(initial_entries, "Last 3 entries before undo:")
        
        undo_count = 0
        current_entries = initial_entries
        
        while True:
            undo_count += 1
            
            rprint(f"\n[bold blue]⏪ Undoing last timewarrior operation... (attempt {undo_count})[/bold blue]")
            
            # Execute the undo command
            result = subprocess.run(
                ["timew", "undo"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Get entries after this undo
            new_entries = _get_current_entries()
            
            # Check if there's a meaningful difference
            if _entries_have_meaningful_difference(current_entries, new_entries):
                # Meaningful change found, stop here
                _display_entries(new_entries, "\nLast 3 entries after undo:")
                if undo_count > 1:
                    rprint(f"\n[green]✓ Completed {undo_count} undo operations to reach meaningful state change[/green]")
                break
            else:
                # Only annotation/tag changes, continue undoing
                current_entries = new_entries
                _display_entries(new_entries, f"\nLast 3 entries after undo {undo_count}:")
                rprint("[yellow]Only tags/annotations changed, continuing undo...[/yellow]")
                
                # Safety check to prevent infinite loops
                if undo_count >= 10:
                    rprint("[yellow]Stopped after 10 undo operations to prevent infinite loop[/yellow]")
                    break
            
    except subprocess.CalledProcessError as e:
        if "No undo information" in e.stderr or "Nothing to undo" in e.stderr:
            rprint("[yellow]Nothing to undo - no recent operations found[/yellow]")
        else:
            rprint(f"[red]Error during undo: {e.stderr}[/red]")
            raise typer.Exit(1)
    except FileNotFoundError:
        rprint("[red]Error: 'timew' command not found. Make sure timewarrior is installed.[/red]")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
