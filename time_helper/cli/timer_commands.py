"""Timer-related commands for starting, stopping, and managing timers."""

import subprocess
from typing import List, Optional
import typer
from rich import print as rprint

from .utils import run_timew_command, handle_timew_errors, get_current_entries, entries_have_meaningful_difference, display_entries
from ..logging_config import get_logger

logger = get_logger(__name__)


@handle_timew_errors
def start_timer(args: Optional[List[str]] = None) -> None:
    """Start a new timer with optional tags and annotation.
    
    Args:
        args: List of tags and optional annotation
    """
    logger.debug(f"Starting timer with args: {args}")
    
    if not args:
        logger.debug("No args provided, starting timer without tags")
        run_timew_command(["start"], check=True)
        rprint("[bold green]✓ Timer started![/bold green]")
        return
    
    # Parse time from args if present (e.g., 'admin meeting 0700')
    time_arg = None
    filtered_args = []
    
    for arg in args:
        if arg.isdigit() and len(arg) == 4:
            time_arg = f"{arg[:2]}:{arg[2:]}"
            logger.debug(f"Found time argument: {time_arg}")
        else:
            filtered_args.append(arg)
    
    # Build command
    cmd_args = ["start"] + filtered_args
    if time_arg:
        cmd_args.append(time_arg)
    
    logger.debug(f"Running start command: {cmd_args}")
    result = run_timew_command(cmd_args, check=True)
    
    rprint("[bold green]✓ Timer started![/bold green]")
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
def undo_last_action() -> None:
    """Undo the last timewarrior operation and show before/after status.
    
    If the undo only removes tags or annotations, it will repeat the undo 
    until there's a meaningful state change.
    """
    logger.debug("Starting undo operation")
    
    # Get initial state
    initial_entries = get_current_entries()
    display_entries(initial_entries, "Last 3 entries before undo:")
    
    undo_count = 0
    current_entries = initial_entries
    
    while True:
        undo_count += 1
        logger.debug(f"Undo attempt {undo_count}")
        
        rprint(f"\n[bold blue]⏪ Undoing last timewarrior operation... (attempt {undo_count})[/bold blue]")
        
        # Execute the undo command
        run_timew_command(["undo"], check=True)
        
        # Get entries after this undo
        new_entries = get_current_entries()
        
        # Check if there's a meaningful difference
        if entries_have_meaningful_difference(current_entries, new_entries):
            # Meaningful change found, stop here
            display_entries(new_entries, "\nLast 3 entries after undo:")
            if undo_count > 1:
                rprint(f"\n[green]✓ Completed {undo_count} undo operations to reach meaningful state change[/green]")
            logger.info(f"Completed undo operation after {undo_count} attempts")
            break
        else:
            # Only annotation/tag changes, continue undoing
            current_entries = new_entries
            display_entries(new_entries, f"\nLast 3 entries after undo {undo_count}:")
            rprint("[yellow]Only tags/annotations changed, continuing undo...[/yellow]")
            
            # Safety check to prevent infinite loops
            if undo_count >= 10:
                rprint("[yellow]Stopped after 10 undo operations to prevent infinite loop[/yellow]")
                logger.warning("Stopped undo after 10 attempts to prevent infinite loop")
                break


# Create typer commands
def create_timer_commands() -> typer.Typer:
    """Create and return the timer commands typer app."""
    timer_app = typer.Typer(help="Timer management commands")
    
    @timer_app.command("start")
    def start_command(
        args: Optional[List[str]] = typer.Argument(None, help="Tag and optional annotation, with optional time (e.g., 'admin meeting 0700')")
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
