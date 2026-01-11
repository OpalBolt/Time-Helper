"""Tests for report generation and export commands."""

from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from datetime import date

from time_helper.cli import app
from time_helper.cli.report_commands import (
    generate_report,
)  # Import the actual function to mock it

runner = CliRunner()


@patch("time_helper.cli.report_commands.generate_report")
def test_generate_command_start_date(mock_generate_report):
    """Test that the 'generate' command correctly passes --start-date."""
    result = runner.invoke(
        app, ["report", "generate", "--start-date", "2025-01-01", "--no-cache"]
    )
    mock_generate_report.assert_called_once_with(
        week_offset=0,
        year=None,
        date_str=None,  # Existing param, will be default
        use_cache=False,
        start_date=date(2025, 1, 1),
        end_date=None,
        tags=None,
        output_format="terminal",
    )
    assert (
        result.exit_code == 0
    )  # Will technically succeed because we mocked generate_report


@patch("time_helper.cli.report_commands.generate_report")
def test_generate_command_end_date(mock_generate_report):
    """Test that the 'generate' command correctly passes --end-date."""
    result = runner.invoke(
        app, ["report", "generate", "--end-date", "2025-01-07", "--no-cache"]
    )
    mock_generate_report.assert_called_once_with(
        week_offset=0,
        year=None,
        date_str=None,
        use_cache=False,
        start_date=None,
        end_date=date(2025, 1, 7),
        tags=None,
        output_format="terminal",
    )
    assert result.exit_code == 0


@patch("time_helper.cli.report_commands.generate_report")
def test_generate_command_tags(mock_generate_report):
    """Test that the 'generate' command correctly passes --tags."""
    result = runner.invoke(
        app, ["report", "generate", "--tags", "tag1,tag2", "--no-cache"]
    )
    mock_generate_report.assert_called_once_with(
        week_offset=0,
        year=None,
        date_str=None,
        use_cache=False,
        start_date=None,
        end_date=None,
        tags=["tag1", "tag2"],
        output_format="terminal",
    )
    assert result.exit_code == 0


@patch("time_helper.cli.report_commands.generate_report")
def test_generate_command_all_new_options(mock_generate_report):
    """Test that the 'generate' command correctly passes all new options."""
    result = runner.invoke(
        app,
        [
            "report",
            "generate",
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-01-07",
            "--tags",
            "tagA,tagB,tagC",
            "--no-cache",
        ],
    )
    mock_generate_report.assert_called_once_with(
        week_offset=0,
        year=None,
        date_str=None,
        use_cache=False,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 7),
        tags=["tagA", "tagB", "tagC"],
        output_format="terminal",
    )
    assert result.exit_code == 0

@patch("time_helper.cli.report_commands.generate_report")
def test_generate_command_format(mock_generate_report):
    """Test that the 'generate' command correctly passes --format."""
    result = runner.invoke(
        app, ["report", "generate", "--format", "markdown", "--no-cache"]
    )
    mock_generate_report.assert_called_once_with(
        week_offset=0,
        year=None,
        date_str=None,
        use_cache=False,
        start_date=None,
        end_date=None,
        tags=None,
        output_format="markdown",
    )
    assert result.exit_code == 0
