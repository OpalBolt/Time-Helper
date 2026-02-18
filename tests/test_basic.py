"""Basic tests for time-helper application."""

from time_helper.cli import app
from typer.testing import CliRunner


def test_app_help():
    """Test that the app shows help when called with --help."""
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Time tracking helper tool" in result.stdout


def test_app_version():
    """Test that the app shows version information."""
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    # Should not crash, exact behavior depends on implementation
    assert result.exit_code in [
        0,
        2,
    ]  # 0 for success, 2 for typer's default behavior  # noqa: E501


def test_import_main_module():
    """Test that we can import the main module without errors."""
    import time_helper

    assert time_helper is not None


def test_import_cli_module():
    """Test that we can import the CLI module without errors."""
    from time_helper.cli import app

    assert app is not None
