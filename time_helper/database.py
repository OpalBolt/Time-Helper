"""Database operations for time tracking data."""

import sqlite3
import os
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pathlib import Path
from .models import TimeEntry, WeeklyReport, DailyReport, TagSummary


class Database:
    """Handle SQLite database operations for time tracking data."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection and create tables if needed."""
        if db_path is None:
            db_path = self._get_default_db_path()
        self.db_path = Path(db_path)
        # Ensure the directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _get_default_db_path(self) -> str:
        """Get the default database path in a central location."""
        # Allow override via environment variable
        env_path = os.environ.get("TIME_HELPER_DB_PATH")
        if env_path:
            return env_path

        # Use XDG Base Directory Specification on Linux/Unix
        if os.name == "posix":
            # Use XDG_DATA_HOME if set, otherwise default to ~/.local/share
            data_home = os.environ.get("XDG_DATA_HOME")
            if data_home:
                base_dir = Path(data_home)
            else:
                base_dir = Path.home() / ".local" / "share"
        # Use AppData on Windows
        elif os.name == "nt":
            app_data = os.environ.get("APPDATA")
            if app_data:
                base_dir = Path(app_data)
            else:
                base_dir = Path.home() / "AppData" / "Roaming"
        # Fallback for other systems
        else:
            base_dir = Path.home() / ".local" / "share"

        # Create time-helper specific directory
        app_dir = base_dir / "time-helper"
        return str(app_dir / "time_helper.db")

    def init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS time_entries (
                    id INTEGER,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    tag TEXT NOT NULL,
                    annotation TEXT,
                    date TEXT NOT NULL,
                    hours REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id, date)
                );
                
                CREATE TABLE IF NOT EXISTS weekly_reports (
                    week_start TEXT PRIMARY KEY,
                    report_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_time_entries_date ON time_entries(date);
                CREATE INDEX IF NOT EXISTS idx_time_entries_tag ON time_entries(tag);
            """
            )

    def store_time_entries(self, entries: List[TimeEntry], entry_date: date) -> None:
        """Store time entries in the database."""
        with sqlite3.connect(self.db_path) as conn:
            for entry in entries:
                tag = entry.get_primary_tag()
                hours = entry.get_duration_hours()

                conn.execute(
                    """
                    INSERT OR REPLACE INTO time_entries 
                    (id, start_time, end_time, tag, annotation, date, hours)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        entry.id,
                        entry.start,
                        entry.end,
                        tag,
                        entry.annotation,
                        entry_date.isoformat(),
                        hours,
                    ),
                )

    def get_time_entries(self, start_date: date, end_date: date) -> List[TimeEntry]:
        """Get time entries for a date range."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, start_time, end_time, tag, annotation, date
                FROM time_entries
                WHERE date BETWEEN ? AND ?
                ORDER BY date, start_time
            """,
                (start_date.isoformat(), end_date.isoformat()),
            )

            entries = []
            for row in cursor.fetchall():
                entry = TimeEntry(
                    id=row[0],
                    start=row[1],
                    end=row[2],
                    tags=[row[3]],  # Single tag as list
                    annotation=row[4],
                    date=datetime.fromisoformat(row[5]).date(),
                )
                entries.append(entry)

            return entries

    def get_weekly_report(self, week_start: date) -> Optional[WeeklyReport]:
        """Get cached weekly report."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT report_data FROM weekly_reports
                WHERE week_start = ?
            """,
                (week_start.isoformat(),),
            )

            row = cursor.fetchone()
            if row:
                # For now, return None as we'd need to serialize/deserialize the report
                # This is a placeholder for actual implementation
                return None

            return None

    def store_weekly_report(self, report: WeeklyReport) -> None:
        """Store weekly report in cache."""
        # Placeholder for actual implementation
        # Would need to serialize the report object
        pass

    def get_all_tags(self) -> List[Dict[str, Any]]:
        """Get all unique tags with statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT 
                    tag,
                    SUM(hours) as total_hours,
                    MAX(date) as last_used
                FROM time_entries
                GROUP BY tag
                ORDER BY total_hours DESC
            """
            )

            tags = []
            for row in cursor.fetchall():
                tags.append(
                    {
                        "tag": row[0],
                        "total_hours": row[1],
                        "last_used": (
                            datetime.fromisoformat(row[2]).date() if row[2] else None
                        ),
                    }
                )

            return tags
