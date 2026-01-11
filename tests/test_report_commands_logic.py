import pytest
from unittest.mock import patch, MagicMock
from datetime import date
from time_helper.cli.report_commands import generate_report

@patch("time_helper.cli.report_commands.Database")
@patch("time_helper.cli.report_commands.ReportGenerator")
@patch("time_helper.cli.report_commands.WeekUtils")
def test_generate_report_logic_with_filters(mock_week_utils, mock_report_generator, mock_database):
    """Test that generate_report passes filters to Database and ReportGenerator."""
    # Setup mocks
    db_instance = mock_database.return_value
    report_gen_instance = mock_report_generator.return_value
    
    # Mock db.get_time_entries to return something so we don't trigger export
    db_instance.get_time_entries.return_value = ["fake_entry"]
    
    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 3)
    tags = ["work"]
    
    # Call function
    generate_report(start_date=start_date, end_date=end_date, tags=tags, use_cache=True)
    
    # Verify calls
    # Note: args passed to generate_report are positional or keyword depending on implementation
    # We check if called with correct args
    db_instance.get_time_entries.assert_called_with(start_date, end_date, tags=tags)
    report_gen_instance.generate_report.assert_called_with(["fake_entry"], start_date, end_date, tags=tags)
    report_gen_instance.print_weekly_report.assert_called()

@patch("time_helper.cli.report_commands.Database")
@patch("time_helper.cli.report_commands.ReportGenerator")
@patch("time_helper.cli.report_commands._export_day_data")
def test_generate_report_logic_export(mock_export, mock_report_generator, mock_database):
    """Test that generate_report triggers export when cache is empty/disabled."""
    db_instance = mock_database.return_value
    
    # Mock cache miss
    db_instance.get_time_entries.return_value = []
    
    mock_export.return_value = [] # Return empty for simplicity, or mock entries
    
    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 1) # Single day
    
    # Call function
    generate_report(start_date=start_date, end_date=end_date, use_cache=True)
    
    # Verify export was called
    mock_export.assert_called()
