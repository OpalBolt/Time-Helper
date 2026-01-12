import pytest
from datetime import date
from time_helper.report_generator import ReportGenerator
from time_helper.models import TimeEntry, WeeklyReport, DailyReport, TagSummary

def test_format_as_markdown_exists():
    generator = ReportGenerator()
    assert hasattr(generator, 'format_as_markdown'), "ReportGenerator should have 'format_as_markdown' method"

def test_format_as_markdown_content():
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
    
    markdown = generator.format_as_markdown(report)
    
    assert "# Time Report" in markdown
    assert "January 12" in markdown
    assert "## Daily Reports" in markdown
    assert "### Monday (2026-01-12)" in markdown
    assert "| Tag | Hours | Annotations |" in markdown
    assert "| work | 1.00 | Test task |" in markdown
    assert "## Weekly Summary" in markdown
    assert "| Tag | Total Hours | Daily Breakdown |" in markdown
    assert "**Total Hours: 1.00 hours**" in markdown

def test_format_as_markdown_empty():
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
    
    markdown = generator.format_as_markdown(report)
    
    assert "# Time Report" in markdown
    assert "## Daily Reports" in markdown
    assert "## Weekly Summary" in markdown
    assert "*No time tracked this week*" in markdown

def test_format_as_markdown_empty_day():
    generator = ReportGenerator()
    
    start_date = date(2026, 1, 12)
    end_date = date(2026, 1, 18)
    
    daily_report = DailyReport(
        date=start_date,
        tag_summaries={},
        total_hours=0.0
    )
    
    report = WeeklyReport(
        week_start=start_date,
        daily_reports={start_date: daily_report},
        weekly_summaries={},
        total_hours=0.0,
        end_date=end_date
    )
    
    markdown = generator.format_as_markdown(report)
    
    assert "### Monday (2026-01-12)" in markdown
    assert "*No time tracked*" in markdown
