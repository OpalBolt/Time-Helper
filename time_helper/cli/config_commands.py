"""CLI commands for configuration management."""

import typer
from rich.console import Console
from rich.table import Table

from ..config import Config, get_config_path
from ..logging_config import get_logger

logger = get_logger(__name__)
console = Console()


def create_config_commands() -> typer.Typer:
    """Create and return the config command group."""
    app = typer.Typer(help="Configuration management")

    @app.command("list-schemes")
    def list_schemes():
        """List all available color schemes."""
        config = Config.load()
        schemes = Config.get_available_schemes()

        table = Table(title="Available Color Schemes", show_header=True)
        table.add_column("Name", style="cyan")
        table.add_column("Colors", style="dim")
        table.add_column("Current", style="green")

        for name, scheme in schemes.items():
            # Show first few colors as preview
            color_preview = ", ".join(scheme.colors[:4])
            if len(scheme.colors) > 4:
                color_preview += "..."

            is_current = "✓" if name == config.color_scheme else ""
            table.add_row(name, color_preview, is_current)

        console.print(table)
        console.print(
            f"\nCurrent scheme: [bold]{config.color_scheme}[/bold]",
            style="green",
        )

    @app.command("set-scheme")
    def set_scheme(
        scheme: str = typer.Argument(
            ...,
            help="Name of the color scheme to use",
        ),
    ):
        """Set the active color scheme."""
        try:
            config = Config.load()
            # This will validate the scheme name via Pydantic
            config.color_scheme = scheme
            config.save()
            console.print(
                f"✓ Color scheme set to: [bold]{scheme}[/bold]",
                style="green",
            )
            logger.info(f"Color scheme changed to: {scheme}")
        except ValueError as e:
            console.print(f"[red]Error:[/red] {str(e)}")
            raise typer.Exit(1)
        except OSError as e:
            logger.error("Failed to save configuration: %s", e)
            console.print(
                "[red]Error:[/red] Failed to write configuration file. "
                "Check file permissions and try again."
            )
            raise typer.Exit(1)

    @app.command("get-scheme")
    def get_scheme():
        """Show the current color scheme."""
        config = Config.load()
        scheme = config.get_scheme()

        console.print(f"Current scheme: [bold]{config.color_scheme}[/bold]")
        console.print(f"\nColors ({len(scheme.colors)} total):")

        # Display colors with examples
        for i, color in enumerate(scheme.colors, 1):
            console.print(f"  {i}. [{color}]{color}[/{color}]")

    @app.command("show-config-path")
    def show_config_path():
        """Show the path to the configuration file."""
        path = get_config_path()
        console.print(f"Configuration file: {path}")
        if path.exists():
            console.print("[green]✓ File exists[/green]")
        else:
            msg = "[yellow]File not created yet (using defaults)[/yellow]"
            console.print(msg)

    @app.command("reset")
    def reset_config():
        """Reset configuration to defaults."""
        confirm = typer.confirm(
            "Are you sure you want to reset configuration to defaults?"
        )
        if not confirm:
            console.print("Cancelled.")
            raise typer.Exit(0)

        try:
            config = Config()  # Create default config
            config.save()
            console.print("[green]✓ Configuration reset to defaults[/green]")
            logger.info("Configuration reset to defaults")
        except OSError as e:
            logger.error("Failed to reset configuration to defaults: %s", e)
            console.print(
                "[red]Error:[/red] Failed to write configuration file. "
                "Check file permissions and try again."
            )
            raise typer.Exit(1)

    return app
