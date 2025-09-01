"""Enhanced report generator with rich formatting and comprehensive weekly reports."""

from typing import List, Dict
from datetime import date, timedelta
from collections import defaultdict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from .models import TimeEntry, WeeklyReport, DailyReport, TagSummary


class ReportGenerator:
    """Generate comprehensive weekly reports with rich formatting."""
    
    def __init__(self):
        self.console = Console()
    
    def generate_weekly_report(self, entries: List[TimeEntry], week_start: date) -> WeeklyReport:
        """Generate a comprehensive weekly report from time entries."""
        
        # Group entries by date and tag
        daily_data: Dict[date, Dict[str, List[TimeEntry]]] = defaultdict(lambda: defaultdict(list))
        weekly_data: Dict[str, List[TimeEntry]] = defaultdict(list)
        
        for entry in entries:
            entry_date = entry.date or week_start  # Fallback to week_start if no date
            tag = entry.get_primary_tag()
            
            daily_data[entry_date][tag].append(entry)
            weekly_data[tag].append(entry)
        
        # Generate daily reports
        daily_reports: Dict[date, DailyReport] = {}
        
        for day_date, day_tags in daily_data.items():
            tag_summaries: Dict[str, TagSummary] = {}
            daily_total = 0.0
            
            for tag, tag_entries in day_tags.items():
                total_hours = sum(entry.get_duration_hours() for entry in tag_entries)
                annotations = [entry.annotation for entry in tag_entries if entry.annotation]
                
                tag_summaries[tag] = TagSummary(
                    tag=tag,
                    total_hours=total_hours,
                    entries=tag_entries,
                    annotations=annotations
                )
                daily_total += total_hours
            
            daily_reports[day_date] = DailyReport(
                date=day_date,
                tag_summaries=tag_summaries,
                total_hours=daily_total
            )
        
        # Generate weekly summaries
        weekly_summaries: Dict[str, TagSummary] = {}
        total_weekly_hours = 0.0
        
        for tag, tag_entries in weekly_data.items():
            total_hours = sum(entry.get_duration_hours() for entry in tag_entries)
            annotations = [entry.annotation for entry in tag_entries if entry.annotation]
            
            weekly_summaries[tag] = TagSummary(
                tag=tag,
                total_hours=total_hours,
                entries=tag_entries,
                annotations=annotations
            )
            total_weekly_hours += total_hours
        
        return WeeklyReport(
            week_start=week_start,
            daily_reports=daily_reports,
            weekly_summaries=weekly_summaries,
            total_hours=total_weekly_hours
        )
    
    def print_weekly_report(self, report: WeeklyReport) -> None:
        """Print a comprehensive weekly report with rich formatting."""
        
        # Header
        title = f"Weekly Time Report - {report.get_week_range_string()}"
        rprint(f"\n[bold blue]{title}[/bold blue]\n")
        
        # Daily reports
        for daily_report in report.get_sorted_daily_reports():
            self._print_daily_report(daily_report)
            rprint()  # Empty line between days
        
        # Weekly summary
        self._print_weekly_summary(report)
    
    def _print_daily_report(self, daily_report: DailyReport) -> None:
        """Print a single day's report."""
        day_header = f"{daily_report.get_day_name()} ({daily_report.get_formatted_date()}):"
        rprint(f"[bold green]{day_header}[/bold green]")
        
        if not daily_report.tag_summaries:
            rprint("  [dim]No time tracked[/dim]")
            return
        
        # Sort tags by hours (descending)
        sorted_tags = sorted(
            daily_report.tag_summaries.values(),
            key=lambda x: x.total_hours,
            reverse=True
        )
        
        for tag_summary in sorted_tags:
            # Tag line with hours
            tag_color = self._get_tag_color(tag_summary.tag)
            rprint(f"  [{tag_color}]{tag_summary.tag}: {tag_summary.total_hours:.2f} hours[/{tag_color}]")
            
            # Annotation lines
            annotations = tag_summary.get_formatted_annotations()
            for annotation in annotations:
                rprint(f"    [dim]{annotation}[/dim]")
        
        # Daily total
        rprint(f"[bold]Daily Total: {daily_report.total_hours:.2f} hours[/bold]")
    
    def _print_weekly_summary(self, report: WeeklyReport) -> None:
        """Print the weekly summary section."""
        rprint("[bold blue]Weekly Summary:[/bold blue]")
        
        if not report.weekly_summaries:
            rprint("  [dim]No time tracked this week[/dim]")
            return
        
        # Create a table for the weekly summary
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Tag", style="cyan", width=20)
        table.add_column("Total Hours", justify="right", style="green")
        table.add_column("Daily Breakdown", style="yellow")
        
        for tag_summary in report.get_sorted_weekly_summaries():
            # Calculate daily breakdown
            daily_breakdown = self._get_daily_breakdown(tag_summary.tag, report.daily_reports)
            
            table.add_row(
                tag_summary.tag,
                f"{tag_summary.total_hours:.2f}",
                daily_breakdown
            )
        
        self.console.print(table)
        
        # Total hours
        rprint(f"\n[bold green]Total Hours: {report.total_hours:.2f} hours[/bold green]")
    
    def _get_daily_breakdown(self, tag: str, daily_reports: Dict[date, DailyReport]) -> str:
        """Get daily breakdown string for a tag."""
        breakdown_parts = []
        
        for report_date in sorted(daily_reports.keys()):
            daily_report = daily_reports[report_date]
            if tag in daily_report.tag_summaries:
                hours = daily_report.tag_summaries[tag].total_hours
                day_abbrev = report_date.strftime("%a")
                breakdown_parts.append(f"{day_abbrev}: {hours:.2f}")
        
        return ", ".join(breakdown_parts) if breakdown_parts else "No hours"
    
    def _get_tag_color(self, tag: str) -> str:
        """Get a consistent color for a tag based on its name."""
        # Simple hash-based color assignment
        colors = [
            "red", "green", "yellow", "blue", "magenta", "cyan",
            "bright_red", "bright_green", "bright_yellow", "bright_blue",
            "bright_magenta", "bright_cyan"
        ]
        
        color_index = hash(tag) % len(colors)
        return colors[color_index]
