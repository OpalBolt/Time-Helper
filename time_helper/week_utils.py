"""Utilities for handling weeks and dates."""

from datetime import date, timedelta
from typing import List


class WeekUtils:
    """Utility functions for working with weeks."""

    @staticmethod
    def get_week_start(target_date: date) -> date:
        """Get the Monday of the week containing the target date."""
        days_since_monday = target_date.weekday()
        return target_date - timedelta(days=days_since_monday)

    @staticmethod
    def get_week_dates(week_start: date) -> List[date]:
        """Get all 7 dates for a week starting from Monday."""
        return [week_start + timedelta(days=i) for i in range(7)]

    @staticmethod
    def get_week_start_date(week_offset: int, year: int) -> date:
        """Get the start date of a week based on offset from current week."""
        today = date.today()
        current_week_start = WeekUtils.get_week_start(today)
        target_week_start = current_week_start + timedelta(weeks=week_offset)

        # If year is specified and different from calculated year, adjust
        if year != target_week_start.year:
            # Find the first Monday of the specified year
            jan_1 = date(year, 1, 1)
            first_monday = WeekUtils.get_week_start(jan_1)
            if first_monday.year < year:
                first_monday += timedelta(weeks=1)

            # Apply the same week offset from the first Monday of that year
            current_week_number = (
                current_week_start - WeekUtils.get_week_start(date(today.year, 1, 1))
            ).days // 7
            target_week_start = first_monday + timedelta(
                weeks=current_week_number + week_offset
            )

        return target_week_start

    @staticmethod
    def format_week_range(week_start: date) -> str:
        """Format a week range string."""
        week_end = week_start + timedelta(days=6)
        return f"{week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}"
