"""Timer-related commands for starting, stopping, and managing timers."""

import readline
import subprocess
import sys
from typing import List, Optional
import typer
from rich import print as rprint

from .utils import (
    run_timew_command,
    handle_timew_errors,
    get_current_entries,
    entries_have_meaningful_difference,
    display_entries,
)
from ..database import Database
from ..logging_config import get_logger
from ..exceptions import TimewarriorError, TimeHelperError

logger = get_logger(__name__)


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
        except Exception:
            pass


@handle_timew_errors
def start_timer(args: Optional[List[str]] = None) -> None:
    """Start a new timer with optional tags and annotation.

    Args:
        args: List of tags and optional annotation
    """
    logger.debug(f"Starting timer with args: {args}")

    if not args:
        # Interactive mode - get input from user with tag completion
        logger.debug("No args provided, starting interactive timer")
        rprint("[bold blue]Starting new timer...[/bold blue]")

        # Get available tags for completion
        try:
            db = Database()
            tag_data = db.get_all_tags()
            available_tags = [tag["tag"] for tag in tag_data]
        except Exception:
            # Fallback if database is not available
            available_tags = []

        # Get user input with tab completion
        prompt_text = "Enter tag and optional annotation (tag annotation): "
        user_input = get_user_input_with_completion(prompt_text, available_tags).strip()

        if not user_input:
            raise TimeHelperError("Tag cannot be empty")

        # Parse interactive input into args
        args = user_input.split()

    # Parse time from args if present (e.g., 'admin meeting 0700')
    time_arg = None
    filtered_args = []

    for arg in args:
        if arg.isdigit() and len(arg) == 4:
            time_arg = f"{arg[:2]}:{arg[2:]}"
            logger.debug(f"Found time argument: {time_arg}")
        else:
            filtered_args.append(arg)

    # First argument is the tag, rest are annotation
    if not filtered_args:
        raise TimeHelperError("No tag provided")

    tag = filtered_args[0].lower()  # Normalize tag to lowercase
    annotation = " ".join(filtered_args[1:]) if len(filtered_args) > 1 else ""

    rprint(f"[green]Tag: {tag}[/green]")
    if annotation:
        rprint(f"[green]Annotation: {annotation}[/green]")
    if time_arg:
        rprint(f"[green]Start time: {time_arg}[/green]")

    # Build timew command - only the tag goes to start command
    cmd_args = ["start", tag]
    if time_arg:
        # First try without :adjust to detect overlaps
        test_cmd = cmd_args + [time_arg]
        logger.debug(f"Testing for overlaps with command: {test_cmd}")

        try:
            # Test the command without :adjust first
            run_timew_command(test_cmd, check=True)
            # If it succeeds, no overlap - use the command as-is
            cmd_args.append(time_arg)
        except TimewarriorError as e:
            error_msg = str(e)
            if "You cannot overlap intervals" in error_msg:
                # There's an overlap - ask for confirmation before using :adjust
                rprint(
                    f"[yellow]⚠️  The start time {time_arg} would overlap with existing intervals.[/yellow]"
                )

                # Show only the entries that would actually be impacted
                try:
                    from datetime import time as Time

                    # Parse the input time (handle formats like "06:40" or "0640")
                    time_str = time_arg.replace(":", "")  # Remove colon if present
                    if len(time_str) == 4 and time_str.isdigit():
                        input_hour = int(time_str[:2])
                        input_minute = int(time_str[2:])
                        input_time = Time(input_hour, input_minute)
                    else:
                        raise ValueError(f"Invalid time format: {time_arg}")

                    # Get today's entries and find impacted ones
                    current_entries = get_current_entries()
                    impacted_entries = []

                    logger.debug(
                        f"Checking {len(current_entries)} entries for impact with input time {input_time}"
                    )

                    # Process entries in chronological order (oldest first)
                    for entry in reversed(current_entries):
                        entry_start = entry.parse_start().time()
                        entry_end = entry.parse_end()

                        logger.debug(
                            f"Entry {entry.id}: {entry_start} - {entry_end.time() if entry_end else 'ongoing'} tags: {entry.tags}"
                        )

                        if entry_end is None:
                            # Active timer - would be impacted if input time is before its start
                            if input_time <= entry_start:
                                logger.debug(
                                    f"Entry {entry.id} would be impacted (active timer would be stopped)"
                                )
                                impacted_entries.append(entry)
                        else:
                            entry_end_time = entry_end.time()
                            # Entry would be impacted if input time falls within its interval
                            if entry_start <= input_time < entry_end_time:
                                logger.debug(
                                    f"Entry {entry.id} would be impacted (would be shortened)"
                                )
                                impacted_entries.append(entry)
                            elif input_time < entry_start:
                                # Starting before this entry - this entry would be impacted
                                logger.debug(
                                    f"Entry {entry.id} would be impacted (starts after input time)"
                                )
                                impacted_entries.append(entry)
                            else:
                                logger.debug(
                                    f"Entry {entry.id} not impacted (ends before input time)"
                                )

                    logger.debug(f"Found {len(impacted_entries)} impacted entries")

                    if impacted_entries:
                        # Show impacted entries in the original order (newest first) to match undo format
                        # Limit to first 8 entries to avoid overwhelming output
                        entries_to_show = list(reversed(impacted_entries))[:8]
                        display_entries(
                            entries_to_show,
                            "Entries that would be impacted:",
                        )

                        if len(impacted_entries) > 8:
                            rprint(
                                f"[dim]... and {len(impacted_entries) - 8} more entries[/dim]"
                            )
                    else:
                        logger.debug(
                            "No impacted entries found, this might be a logic error"
                        )

                except Exception as ex:
                    logger.debug(f"Failed to analyze impacted entries: {ex}")
                    # Fallback to showing recent entries
                    current_entries = get_current_entries()
                    if current_entries and len(current_entries) > 0:
                        display_entries(current_entries[-2:], "Recent entries:")

                confirm = typer.confirm("Automatically adjust conflicting intervals?")
                if confirm:
                    cmd_args.extend([time_arg, ":adjust"])
                    rprint("[dim]Using :adjust to resolve overlaps...[/dim]")
                else:
                    rprint("[yellow]Timer start cancelled.[/yellow]")
                    return
            elif "cannot be set in the future" in error_msg:
                # Provide a hint for future time
                raise TimeHelperError(
                    f"{error_msg}\n[yellow]Hint: Provide a past or current time.[/yellow]"
                )
            else:
                # Some other error - re-raise
                raise

    logger.debug(f"Running start command: {cmd_args}")

    try:
        result = run_timew_command(cmd_args, check=True)
    except TimewarriorError as e:
        error_msg = str(e)
        if "You cannot overlap intervals" in error_msg:
            # Provide helpful guidance for overlaps that couldn't be auto-resolved
            rprint("[yellow]⚠️  Cannot start timer - time overlap detected[/yellow]")
            rprint(
                "[dim]The specified start time conflicts with existing time intervals.[/dim]"
            )
            rprint("[dim]Options:[/dim]")
            rprint("[dim]  • Stop current tracking: [/dim][cyan]timew stop[/cyan]")
            rprint("[dim]  • Check active timers: [/dim][cyan]timew[/cyan]")
            rprint("[dim]  • View recent intervals: [/dim][cyan]timew summary[/cyan]")
            rprint("[dim]  • Manually resolve with: [/dim][cyan]timew modify[/cyan]")
            return
        else:
            # Re-raise other errors to be handled by decorator
            raise

    # Add annotation if provided
    if annotation:
        annotate_cmd = ["annotate", annotation]
        logger.debug(f"Running annotate command: {annotate_cmd}")
        run_timew_command(annotate_cmd, check=True)

    rprint("[bold green]✓ Timer started successfully![/bold green]")
    if result.stdout.strip():
        rprint(f"[dim]{result.stdout.strip()}[/dim]")


@handle_timew_errors
def stop_timer() -> None:
    """Stop the currently active timer."""
    logger.debug("Stopping timer")

    result = run_timew_command(["stop"], check=True)
    rprint("[bold green]✓ Timer stopped successfully![/bold green]")

    if result.stdout.strip():
        rprint(f"[dim]{result.stdout.strip()}[/dim]")


@handle_timew_errors
def undo_last_action(single_operation: bool = False) -> None:
    """Undo the last timewarrior operation and show before/after status.

    Args:
        single_operation: If True, only perform one undo operation regardless of meaningfulness

    If single_operation is False and the undo only removes tags or annotations,
    it will repeat the undo until there's a meaningful state change.
    """
    logger.debug(f"Starting undo operation (single_operation={single_operation})")

    # Get initial state
    initial_entries = get_current_entries()
    display_entries(initial_entries, "Last 3 entries before undo:")

    undo_count = 0
    current_entries = initial_entries

    while True:
        undo_count += 1
        logger.debug(f"Undo attempt {undo_count}")

        rprint(
            f"\n[bold blue]⏪ Undoing last timewarrior operation... (attempt {undo_count})[/bold blue]"
        )

        # Execute the undo command
        run_timew_command(["undo"], check=True)

        # Get entries after this undo
        new_entries = get_current_entries()

        # If single_operation is True, stop after one undo regardless of meaningfulness
        if single_operation:
            display_entries(new_entries, "\nLast 3 entries after undo:")
            rprint("\n[green]✓ Undid last annotation change[/green]")
            logger.info("Completed single undo operation")
            break

        # Check if there's a meaningful difference
        if entries_have_meaningful_difference(current_entries, new_entries):
            # Meaningful change found, stop here
            display_entries(new_entries, "\nLast 3 entries after undo:")
            if undo_count > 1:
                rprint(
                    f"\n[green]✓ Completed {undo_count} undo operations to reach meaningful state change[/green]"
                )
            logger.info(f"Completed undo operation after {undo_count} attempts")
            break
        else:
            # Only annotation/tag changes, continue undoing
            current_entries = new_entries
            display_entries(new_entries, f"\nLast 3 entries after undo {undo_count}:")
            rprint("[yellow]Only tags/annotations changed, continuing undo...[/yellow]")

            # Safety check to prevent infinite loops
            if undo_count >= 10:
                rprint(
                    "[yellow]Stopped after 10 undo operations to prevent infinite loop[/yellow]"
                )
                logger.warning(
                    "Stopped undo after 10 attempts to prevent infinite loop"
                )
                break


# Create typer commands
def create_timer_commands() -> typer.Typer:
    """Create and return the timer commands typer app."""
    timer_app = typer.Typer(help="Timer management commands")

    @timer_app.command("start")
    def start_command(
        args: Optional[List[str]] = typer.Argument(
            None,
            help="Tag and optional annotation, with optional time (e.g., 'admin meeting 0700')",
        )
    ) -> None:
        """Start a new timer with optional tags and time."""
        start_timer(args)

    @timer_app.command("stop")
    def stop_command() -> None:
        """Stop the currently active timer."""
        stop_timer()

    @timer_app.command("undo")
    def undo_command() -> None:
        """Undo the last timewarrior operation and show before/after status."""
        undo_last_action()

    return timer_app
