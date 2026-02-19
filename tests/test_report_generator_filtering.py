from datetime import date
from time_helper.report_generator import ReportGenerator


def test_generate_report_with_filters():
    generator = ReportGenerator()
    entries = []
    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 3)
    tags = ["work"]

    # We expect a new method or updated signature that accepts range and tags
    # and returns a report object that has these attributes.
    # Currently generate_weekly_report takes (entries, week_start)

    # Calling the new method (to be implemented)
    report = generator.generate_report(
        entries, start_date, end_date, tags=tags
    )  # noqa: E501

    assert report.start_date == start_date
    assert report.end_date == end_date
    assert report.tags == tags
