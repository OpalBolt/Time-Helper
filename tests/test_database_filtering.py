import pytest
from datetime import date
from time_helper.database import Database
from time_helper.models import TimeEntry


@pytest.fixture
def temp_db(tmp_path):
    db_path = tmp_path / "test_time_helper.db"
    db = Database(str(db_path))
    return db


def test_get_time_entries_filtering(temp_db):
    # Setup data
    entries = [
        TimeEntry(
            id=1,
            start="20230101T090000Z",
            end="20230101T100000Z",
            tags=["work"],
            annotation="Task 1",
            date=date(2023, 1, 1),
        ),
        TimeEntry(
            id=2,
            start="20230101T100000Z",
            end="20230101T110000Z",
            tags=["meeting"],
            annotation="Meeting 1",
            date=date(2023, 1, 1),
        ),
        TimeEntry(
            id=3,
            start="20230102T090000Z",
            end="20230102T100000Z",
            tags=["work"],
            annotation="Task 2",
            date=date(2023, 1, 2),
        ),
        TimeEntry(
            id=4,
            start="20230102T100000Z",
            end="20230102T110000Z",
            tags=["personal"],
            annotation="Break",
            date=date(2023, 1, 2),
        ),
    ]

    # Store entries
    temp_db.store_time_entries([entries[0], entries[1]], date(2023, 1, 1))
    temp_db.store_time_entries([entries[2], entries[3]], date(2023, 1, 2))

    # Test 1: Filter by tag "work"
    # This should return entries 1 and 3
    result_work = temp_db.get_time_entries(
        date(2023, 1, 1), date(2023, 1, 2), tags=["work"]
    )
    assert len(result_work) == 2
    assert all("work" in e.tags for e in result_work)
    assert result_work[0].id == 1
    assert result_work[1].id == 3

    # Test 2: Filter by tag "meeting"
    # This should return entry 2
    result_meeting = temp_db.get_time_entries(
        date(2023, 1, 1), date(2023, 1, 2), tags=["meeting"]
    )
    assert len(result_meeting) == 1
    assert result_meeting[0].id == 2

    # Test 3: Filter by multiple tags ["work", "personal"]
    # This should return entries 1, 3, and 4
    result_multi = temp_db.get_time_entries(
        date(2023, 1, 1), date(2023, 1, 2), tags=["work", "personal"]
    )
    assert len(result_multi) == 3
    ids = sorted([e.id for e in result_multi])
    assert ids == [1, 3, 4]

    # Test 4: Filter by non-existent tag
    result_none = temp_db.get_time_entries(
        date(2023, 1, 1), date(2023, 1, 2), tags=["nonexistent"]
    )
    assert len(result_none) == 0

    # Test 5: Default behavior (no tags specified) - should return all
    result_all = temp_db.get_time_entries(date(2023, 1, 1), date(2023, 1, 2))
    assert len(result_all) == 4
