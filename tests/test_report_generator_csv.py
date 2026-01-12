import pytest
import io
import csv
from datetime import date
from time_helper.report_generator import ReportGenerator
from time_helper.models import TimeEntry, WeeklyReport, DailyReport, TagSummary

def test_format_as_csv_exists():
    generator = ReportGenerator()
    assert hasattr(generator, 'format_as_csv'), "ReportGenerator should have 'format_as_csv' method"

def test_format_as_csv_content():
    generator = ReportGenerator()
    
    # Create a mock WeeklyReport
    start_date = date(2026, 1, 12)
    end_date = date(2026, 1, 18)
    
    entry = TimeEntry(
        id=1,
        start="20260112T090000Z",
        end="20260112T100000Z",
        tags=["work"],
        annotation="Test task",
        date=start_date
    )
    
    tag_summary = TagSummary(
        tag="work",
        total_hours=1.0,
        entries=[entry],
        annotations=["Test task"]
    )
    
    daily_report = DailyReport(
        date=start_date,
        tag_summaries={"work": tag_summary},
        total_hours=1.0
    )
    
    report = WeeklyReport(
        week_start=start_date,
        daily_reports={start_date: daily_report},
        weekly_summaries={"work": tag_summary},
        total_hours=1.0,
        end_date=end_date
    )
    
    csv_output = generator.format_as_csv(report)
    
    # Parse CSV to verify content
    f = io.StringIO(csv_output)
    reader = csv.DictReader(f)
    rows = list(reader)
    
    assert len(rows) == 1
    assert rows[0]["Date"] == "2026-01-12"
    assert rows[0]["Tag"] == "work"
    assert rows[0]["Hours"] == "1.00"
    assert rows[0]["Annotations"] == "Test task"

def test_format_as_csv_empty():
    generator = ReportGenerator()
    
    start_date = date(2026, 1, 12)
    end_date = date(2026, 1, 18)
    
    report = WeeklyReport(
        week_start=start_date,
        daily_reports={},
        weekly_summaries={},
        total_hours=0.0,
        end_date=end_date
    )
    
    csv_output = generator.format_as_csv(report)
    f = io.StringIO(csv_output)
    reader = csv.DictReader(f)
    rows = list(reader)
    
    assert len(rows) == 0
