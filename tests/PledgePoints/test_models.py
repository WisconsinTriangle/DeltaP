"""Unit tests for PledgePoints models."""

from datetime import datetime
import pytest

from PledgePoints.models import PointEntry


class TestPointEntry:
    """Tests for PointEntry dataclass."""

    def test_point_entry_creation(self):
        """Test creating a basic PointEntry."""
        time = datetime.now()
        entry = PointEntry(
            time=time,
            point_change=10,
            pledge="John",
            brother="Mike",
            comment="Great work",
        )

        assert entry.time == time
        assert entry.point_change == 10
        assert entry.pledge == "John"
        assert entry.brother == "Mike"
        assert entry.comment == "Great work"
        assert entry.entry_id is None
        assert entry.approval_status == "pending"
        assert entry.approved_by is None
        assert entry.approval_timestamp is None

    def test_point_entry_with_approval(self):
        """Test creating a PointEntry with approval information."""
        time = datetime.now()
        approval_time = datetime.now()
        entry = PointEntry(
            time=time,
            point_change=10,
            pledge="John",
            brother="Mike",
            comment="Great work",
            entry_id=1,
            approval_status="approved",
            approved_by="Admin",
            approval_timestamp=approval_time,
        )

        assert entry.entry_id == 1
        assert entry.approval_status == "approved"
        assert entry.approved_by == "Admin"
        assert entry.approval_timestamp == approval_time

    def test_to_tuple(self):
        """Test converting PointEntry to tuple format."""
        time = datetime.now()
        entry = PointEntry(
            time=time,
            point_change=10,
            pledge="John",
            brother="Mike",
            comment="Great work",
        )

        result = entry.to_tuple()
        assert isinstance(result, tuple)
        assert len(result) == 5
        assert result == (time, 10, "John", "Mike", "Great work")

    def test_from_db_row(self):
        """Test creating PointEntry from a database row."""
        time_str = "2024-01-15T10:30:00"
        approval_time_str = "2024-01-15T11:00:00"

        row = (
            1,  # id
            time_str,  # time
            10,  # point_change
            "John",  # pledge
            "Mike",  # brother
            "Great work",  # comment
            "approved",  # approval_status
            "Admin",  # approved_by
            approval_time_str,  # approval_timestamp
        )

        entry = PointEntry.from_db_row(row)

        assert entry.entry_id == 1
        assert entry.time == datetime.fromisoformat(time_str)
        assert entry.point_change == 10
        assert entry.pledge == "John"
        assert entry.brother == "Mike"
        assert entry.comment == "Great work"
        assert entry.approval_status == "approved"
        assert entry.approved_by == "Admin"
        assert entry.approval_timestamp == datetime.fromisoformat(approval_time_str)

    def test_from_db_row_with_datetime_objects(self):
        """Test from_db_row when time is already a datetime object."""
        time_obj = datetime.now()
        approval_time_obj = datetime.now()

        row = (
            1,
            time_obj,  # Already a datetime
            10,
            "John",
            "Mike",
            "Great work",
            "approved",
            "Admin",
            approval_time_obj,  # Already a datetime
        )

        entry = PointEntry.from_db_row(row)

        assert entry.time == time_obj
        assert entry.approval_timestamp == approval_time_obj

    def test_from_db_row_without_approval(self):
        """Test from_db_row with pending status and no approval data."""
        time_str = "2024-01-15T10:30:00"

        row = (
            1,
            time_str,
            10,
            "John",
            "Mike",
            "Great work",
            "pending",
            None,  # no approver
            None,  # no approval timestamp
        )

        entry = PointEntry.from_db_row(row)

        assert entry.approval_status == "pending"
        assert entry.approved_by is None
        assert entry.approval_timestamp is None

    def test_from_db_row_with_invalid_approval_timestamp(self):
        """Test from_db_row with invalid approval timestamp."""
        time_str = "2024-01-15T10:30:00"

        row = (
            1,
            time_str,
            10,
            "John",
            "Mike",
            "Great work",
            "approved",
            "Admin",
            "invalid-timestamp",  # Invalid format
        )

        entry = PointEntry.from_db_row(row)

        # Should handle invalid timestamp gracefully
        assert entry.approval_timestamp is None

    def test_from_db_row_with_empty_approval_status(self):
        """Test from_db_row with empty approval status defaults to pending."""
        time_str = "2024-01-15T10:30:00"

        row = (
            1,
            time_str,
            10,
            "John",
            "Mike",
            "Great work",
            None,  # or empty string
            None,
            None,
        )

        entry = PointEntry.from_db_row(row)

        assert entry.approval_status == "pending"

    def test_from_simple_row(self):
        """Test creating PointEntry from a simple database row."""
        time_str = "2024-01-15T10:30:00"

        row = (
            time_str,  # time
            10,  # point_change
            "John",  # pledge
            "Mike",  # brother
            "Great work",  # comment
        )

        entry = PointEntry.from_simple_row(row)

        assert entry.time == datetime.fromisoformat(time_str)
        assert entry.point_change == 10
        assert entry.pledge == "John"
        assert entry.brother == "Mike"
        assert entry.comment == "Great work"
        assert entry.entry_id is None
        assert entry.approval_status == "pending"
        assert entry.approved_by is None
        assert entry.approval_timestamp is None

    def test_from_simple_row_with_datetime_object(self):
        """Test from_simple_row when time is already a datetime object."""
        time_obj = datetime.now()

        row = (
            time_obj,  # Already a datetime
            10,
            "John",
            "Mike",
            "Great work",
        )

        entry = PointEntry.from_simple_row(row)

        assert entry.time == time_obj

    def test_negative_points(self):
        """Test PointEntry with negative points."""
        time = datetime.now()
        entry = PointEntry(
            time=time,
            point_change=-5,
            pledge="John",
            brother="Mike",
            comment="Late to event",
        )

        assert entry.point_change == -5

    def test_rejected_status(self):
        """Test PointEntry with rejected status."""
        time = datetime.now()
        approval_time = datetime.now()
        entry = PointEntry(
            time=time,
            point_change=10,
            pledge="John",
            brother="Mike",
            comment="Great work",
            entry_id=1,
            approval_status="rejected",
            approved_by="Admin",
            approval_timestamp=approval_time,
        )

        assert entry.approval_status == "rejected"