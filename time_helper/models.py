"""Data models for time tracking entries and reports."""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, date as Date, timezone
from pydantic import BaseModel


class TimeEntry(BaseModel):
    """Represents a single time tracking entry."""
    
    id: int
    start: str
    end: Optional[str] = None  # Optional to handle active timers
    tags: List[str]
    annotation: Optional[str] = None
    date: Optional[Date] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimeEntry':
        """Create a TimeEntry from a dictionary."""
        return cls(**data)
    
    def parse_start(self) -> datetime:
        """Parse the start time string to datetime with timezone conversion to local time."""
        utc_dt = datetime.strptime(self.start, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        return utc_dt.astimezone()  # Convert to local timezone
    
    def parse_end(self) -> Optional[datetime]:
        """Parse the end time string to datetime with timezone conversion to local time. Returns None for active timers."""
        if self.end is None:
            return None
        utc_dt = datetime.strptime(self.end, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        return utc_dt.astimezone()  # Convert to local timezone
    
    def get_duration_hours(self) -> float:
        """Calculate duration in hours. For active timers, calculates up to now."""
        start_dt = self.parse_start()
        end_dt = self.parse_end()
        
        if end_dt is None:
            # Active timer - calculate duration up to now (in local timezone)
            end_dt = datetime.now().astimezone()
        
        duration = end_dt - start_dt
        return duration.total_seconds() / 3600
    
    def get_primary_tag(self) -> str:
        """Get the primary (first) tag."""
        return self.tags[0] if self.tags else "untagged"


@dataclass
class TagSummary:
    """Summary information for a single tag."""
    
    tag: str
    total_hours: float
    entries: List[TimeEntry]
    annotations: List[str]
    
    def get_formatted_annotations(self) -> List[str]:
        """Get formatted annotation lines for display."""
        if not self.annotations:
            # Provide generic description based on tag name
            return [f"Work on {self.tag} related tasks"]
        
        # Filter out empty annotations and return unique ones
        unique_annotations = list(dict.fromkeys(
            ann for ann in self.annotations if ann and ann.strip()
        ))
        
        return unique_annotations if unique_annotations else [f"Work on {self.tag} related tasks"]


@dataclass
class DailyReport:
    """Report for a single day."""
    
    date: Date
    tag_summaries: Dict[str, TagSummary]
    total_hours: float
    
    def get_day_name(self) -> str:
        """Get the day name (e.g., 'Monday')."""
        return self.date.strftime("%A")
    
    def get_formatted_date(self) -> str:
        """Get formatted date string."""
        return self.date.strftime("%Y-%m-%d")


@dataclass
class WeeklyReport:
    """Comprehensive weekly report."""
    
    week_start: Date
    daily_reports: Dict[Date, DailyReport]
    weekly_summaries: Dict[str, TagSummary]
    total_hours: float
    
    def get_week_range_string(self) -> str:
        """Get formatted week range string."""
        week_end = self.week_start
        for i in range(6):
            from datetime import timedelta
            week_end = self.week_start + timedelta(days=i)
            if self.week_start + timedelta(days=i) in self.daily_reports:
                week_end = self.week_start + timedelta(days=i)
        
        # Find actual week end from available data
        if self.daily_reports:
            week_end = max(self.daily_reports.keys())
        else:
            from datetime import timedelta
            week_end = self.week_start + timedelta(days=6)
        
        return f"Week of {self.week_start.strftime('%B %d, %Y')}"
    
    def get_sorted_daily_reports(self) -> List[DailyReport]:
        """Get daily reports sorted by date."""
        return [self.daily_reports[date] for date in sorted(self.daily_reports.keys())]
    
    def get_sorted_weekly_summaries(self) -> List[TagSummary]:
        """Get weekly tag summaries sorted by total hours (descending)."""
        return sorted(self.weekly_summaries.values(), key=lambda x: x.total_hours, reverse=True)
