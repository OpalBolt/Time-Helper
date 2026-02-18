import pytest
from unittest.mock import patch, MagicMock
from datetime import date
from time_helper.cli.report_commands import generate_report


@patch("time_helper.cli.report_commands.Database")
@patch("time_helper.cli.report_commands.ReportGenerator")
def test_generate_report_markdown_format(mock_report_generator, mock_database):
    """Test that generate_report calls format_as_markdown when requested."""
    db_instance = mock_database.return_value
    report_gen_instance = mock_report_generator.return_value

    db_instance.get_time_entries.return_value = ["fake_entry"]
    report_gen_instance.format_as_markdown.return_value = "# Markdown Report"

    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 3)

    # We use a patch for 'print' or 'rprint' to verify output if we want,
    # but here we mainly care about the call to ReportGenerator
    with patch("time_helper.cli.report_commands.rprint") as mock_rprint:
        generate_report(
            start_date=start_date,
            end_date=end_date,
            output_format="markdown",
            use_cache=True,
        )

    report_gen_instance.format_as_markdown.assert_called()
    # verify that it didn't call the terminal printer
    report_gen_instance.print_weekly_report.assert_not_called()


@patch("time_helper.cli.report_commands.Database")
@patch("time_helper.cli.report_commands.ReportGenerator")
def test_generate_report_csv_format(mock_report_generator, mock_database):
    """Test that generate_report calls format_as_csv when requested."""
    db_instance = mock_database.return_value
    report_gen_instance = mock_report_generator.return_value

    db_instance.get_time_entries.return_value = ["fake_entry"]
    report_gen_instance.format_as_csv.return_value = "Date,Tag,Hours"

    start_date = date(2023, 1, 1)

    with patch("time_helper.cli.report_commands.rprint") as mock_rprint:
        generate_report(start_date=start_date, output_format="csv", use_cache=True)

    report_gen_instance.format_as_csv.assert_called()
    report_gen_instance.print_weekly_report.assert_not_called()
