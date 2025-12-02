"""Unit tests for PledgePoints database utilities."""

import os
import tempfile
from datetime import datetime

import pytest

from PledgePoints.models import PointEntry
from PledgePoints.sqlutils import DatabaseManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def db_manager(temp_db):
    """Create a DatabaseManager instance with a temporary database."""
    return DatabaseManager(temp_db)


class TestDatabaseManagerInit:
    """Tests for DatabaseManager initialization."""

    def test_database_creation(self, temp_db):
        """Test that database and table are created."""
        manager = DatabaseManager(temp_db)
        assert os.path.exists(temp_db)

        # Verify table exists
        with manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='Points'"
            )
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == "Points"

    def test_database_schema_columns(self, db_manager):
        """Test that all required columns exist in the Points table."""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(Points)")
            columns = {row[1] for row in cursor.fetchall()}

            required_columns = {
                "id",
                "Time",
                "PointChange",
                "Pledge",
                "Brother",
                "Comment",
                "approval_status",
                "approved_by",
                "approval_timestamp",
            }
            assert required_columns.issubset(columns)


class TestAddPointEntries:
    """Tests for adding point entries."""

    def test_add_single_entry(self, db_manager):
        """Test adding a single point entry."""
        entry = PointEntry(
            time=datetime.now(),
            point_change=10,
            pledge="John",
            brother="Mike",
            comment="Great work",
        )

        count = db_manager.add_point_entries([entry])
        assert count == 1

    def test_add_multiple_entries(self, db_manager):
        """Test adding multiple point entries."""
        entries = [
            PointEntry(
                time=datetime.now(),
                point_change=10,
                pledge="John",
                brother="Mike",
                comment="Great work",
            ),
            PointEntry(
                time=datetime.now(),
                point_change=-5,
                pledge="Jane",
                brother="Tom",
                comment="Late to event",
            ),
            PointEntry(
                time=datetime.now(),
                point_change=15,
                pledge="John",
                brother="Sarah",
                comment="Outstanding",
            ),
        ]

        count = db_manager.add_point_entries(entries)
        assert count == 3

    def test_added_entries_have_pending_status(self, db_manager):
        """Test that new entries default to pending status."""
        entry = PointEntry(
            time=datetime.now(),
            point_change=10,
            pledge="John",
            brother="Mike",
            comment="Great work",
        )

        db_manager.add_point_entries([entry])
        pending = db_manager.get_pending_points()

        assert len(pending) == 1
        assert pending[0].approval_status == "pending"


class TestGetPoints:
    """Tests for retrieving point entries."""

    def test_get_all_points_empty(self, db_manager):
        """Test getting points from empty database."""
        points = db_manager.get_all_points()
        assert points == []

    def test_get_all_points(self, db_manager):
        """Test getting all points regardless of status."""
        entries = [
            PointEntry(
                time=datetime.now(),
                point_change=10,
                pledge="John",
                brother="Mike",
                comment="Great work",
            ),
            PointEntry(
                time=datetime.now(),
                point_change=5,
                pledge="Jane",
                brother="Tom",
                comment="Good job",
            ),
        ]
        db_manager.add_point_entries(entries)

        all_points = db_manager.get_all_points()
        assert len(all_points) == 2

    def test_get_pending_points(self, db_manager):
        """Test getting only pending points."""
        entry = PointEntry(
            time=datetime.now(),
            point_change=10,
            pledge="John",
            brother="Mike",
            comment="Great work",
        )
        db_manager.add_point_entries([entry])

        pending = db_manager.get_pending_points()
        assert len(pending) == 1
        assert pending[0].approval_status == "pending"

    def test_get_approved_points_empty(self, db_manager):
        """Test getting approved points when none exist."""
        entry = PointEntry(
            time=datetime.now(),
            point_change=10,
            pledge="John",
            brother="Mike",
            comment="Great work",
        )
        db_manager.add_point_entries([entry])

        approved = db_manager.get_approved_points()
        assert len(approved) == 0

    def test_get_point_by_id(self, db_manager):
        """Test retrieving a specific point by ID."""
        entry = PointEntry(
            time=datetime.now(),
            point_change=10,
            pledge="John",
            brother="Mike",
            comment="Great work",
        )
        db_manager.add_point_entries([entry])

        # Get the entry ID from pending points
        pending = db_manager.get_pending_points()
        point_id = pending[0].entry_id

        retrieved = db_manager.get_point_by_id(point_id)
        assert retrieved is not None
        assert retrieved.entry_id == point_id
        assert retrieved.pledge == "John"

    def test_get_point_by_id_not_found(self, db_manager):
        """Test retrieving a non-existent point returns None."""
        result = db_manager.get_point_by_id(999)
        assert result is None

    def test_get_points_with_status_filter(self, db_manager):
        """Test filtering points by multiple statuses."""
        entries = [
            PointEntry(
                time=datetime.now(),
                point_change=10,
                pledge="John",
                brother="Mike",
                comment="Great work",
            ),
        ]
        db_manager.add_point_entries(entries)

        # Should get pending entry
        pending = db_manager.get_all_points(status_filter=["pending"])
        assert len(pending) == 1

        # Should get no approved entries
        approved = db_manager.get_all_points(status_filter=["approved"])
        assert len(approved) == 0


class TestApprovePoints:
    """Tests for approving point entries."""

    def test_approve_single_point(self, db_manager):
        """Test approving a single point entry."""
        entry = PointEntry(
            time=datetime.now(),
            point_change=10,
            pledge="John",
            brother="Mike",
            comment="Great work",
        )
        db_manager.add_point_entries([entry])

        pending = db_manager.get_pending_points()
        point_id = pending[0].entry_id

        approved = db_manager.approve_points([point_id], "Admin")
        assert len(approved) == 1

        # Verify the entry was actually approved in the database
        retrieved = db_manager.get_point_by_id(point_id)
        assert retrieved.approval_status == "approved"
        assert retrieved.approved_by == "Admin"
        assert retrieved.approval_timestamp is not None

    def test_approve_multiple_points(self, db_manager):
        """Test approving multiple point entries."""
        entries = [
            PointEntry(
                time=datetime.now(),
                point_change=10,
                pledge="John",
                brother="Mike",
                comment="Great work",
            ),
            PointEntry(
                time=datetime.now(),
                point_change=5,
                pledge="Jane",
                brother="Tom",
                comment="Good job",
            ),
        ]
        db_manager.add_point_entries(entries)

        pending = db_manager.get_pending_points()
        point_ids = [p.entry_id for p in pending]

        approved = db_manager.approve_points(point_ids, "Admin")
        assert len(approved) == 2

    def test_approve_empty_list(self, db_manager):
        """Test approving with empty ID list."""
        approved = db_manager.approve_points([], "Admin")
        assert approved == []

    def test_approve_nonexistent_ids(self, db_manager):
        """Test approving non-existent IDs returns empty list."""
        approved = db_manager.approve_points([999, 1000], "Admin")
        assert approved == []

    def test_approve_all_pending(self, db_manager):
        """Test approving all pending points."""
        entries = [
            PointEntry(
                time=datetime.now(),
                point_change=10,
                pledge="John",
                brother="Mike",
                comment="Great work",
            ),
            PointEntry(
                time=datetime.now(),
                point_change=5,
                pledge="Jane",
                brother="Tom",
                comment="Good job",
            ),
        ]
        db_manager.add_point_entries(entries)

        approved = db_manager.approve_all_pending("Admin")
        assert len(approved) == 2

        # Verify no pending points remain
        pending = db_manager.get_pending_points()
        assert len(pending) == 0

    def test_approve_all_pending_when_none_exist(self, db_manager):
        """Test approve_all_pending when no pending points exist."""
        approved = db_manager.approve_all_pending("Admin")
        assert approved == []

    def test_approved_points_persisted(self, db_manager):
        """Test that approved points are properly persisted."""
        entry = PointEntry(
            time=datetime.now(),
            point_change=10,
            pledge="John",
            brother="Mike",
            comment="Great work",
        )
        db_manager.add_point_entries([entry])

        pending = db_manager.get_pending_points()
        point_id = pending[0].entry_id

        db_manager.approve_points([point_id], "Admin")

        # Retrieve from database
        approved_points = db_manager.get_approved_points()
        assert len(approved_points) == 1
        assert approved_points[0].approval_status == "approved"


class TestRejectPoints:
    """Tests for rejecting point entries."""

    def test_reject_single_point(self, db_manager):
        """Test rejecting a single point entry."""
        entry = PointEntry(
            time=datetime.now(),
            point_change=10,
            pledge="John",
            brother="Mike",
            comment="Great work",
        )
        db_manager.add_point_entries([entry])

        pending = db_manager.get_pending_points()
        point_id = pending[0].entry_id

        rejected = db_manager.reject_points([point_id], "Admin")
        assert len(rejected) == 1

        # Verify the entry was actually rejected in the database
        retrieved = db_manager.get_point_by_id(point_id)
        assert retrieved.approval_status == "rejected"

    def test_reject_multiple_points(self, db_manager):
        """Test rejecting multiple point entries."""
        entries = [
            PointEntry(
                time=datetime.now(),
                point_change=10,
                pledge="John",
                brother="Mike",
                comment="Great work",
            ),
            PointEntry(
                time=datetime.now(),
                point_change=5,
                pledge="Jane",
                brother="Tom",
                comment="Good job",
            ),
        ]
        db_manager.add_point_entries(entries)

        pending = db_manager.get_pending_points()
        point_ids = [p.entry_id for p in pending]

        rejected = db_manager.reject_points(point_ids, "Admin")
        assert len(rejected) == 2

    def test_reject_empty_list(self, db_manager):
        """Test rejecting with empty ID list."""
        rejected = db_manager.reject_points([], "Admin")
        assert rejected == []

    def test_reject_all_pending(self, db_manager):
        """Test rejecting all pending points."""
        entries = [
            PointEntry(
                time=datetime.now(),
                point_change=10,
                pledge="John",
                brother="Mike",
                comment="Great work",
            ),
            PointEntry(
                time=datetime.now(),
                point_change=5,
                pledge="Jane",
                brother="Tom",
                comment="Good job",
            ),
        ]
        db_manager.add_point_entries(entries)

        rejected = db_manager.reject_all_pending("Admin")
        assert len(rejected) == 2

        # Verify no pending points remain
        pending = db_manager.get_pending_points()
        assert len(pending) == 0

    def test_reject_all_pending_when_none_exist(self, db_manager):
        """Test reject_all_pending when no pending points exist."""
        rejected = db_manager.reject_all_pending("Admin")
        assert rejected == []

    def test_rejected_not_in_approved(self, db_manager):
        """Test that rejected points don't appear in approved list."""
        entry = PointEntry(
            time=datetime.now(),
            point_change=10,
            pledge="John",
            brother="Mike",
            comment="Great work",
        )
        db_manager.add_point_entries([entry])

        pending = db_manager.get_pending_points()
        point_id = pending[0].entry_id

        db_manager.reject_points([point_id], "Admin")

        approved = db_manager.get_approved_points()
        assert len(approved) == 0


class TestConnectionManagement:
    """Tests for database connection management."""

    def test_connection_context_manager(self, db_manager):
        """Test that connection context manager works properly."""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1

    def test_connection_rollback_on_error(self, db_manager):
        """Test that connection rolls back on error."""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                # This should cause an error
                cursor.execute("INSERT INTO NonExistentTable VALUES (1)")
        except Exception:
            pass  # Expected to fail

        # Database should still be functional
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
