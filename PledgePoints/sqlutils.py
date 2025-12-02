"""
Database manager for the pledge points system.

This module provides a centralized database manager class that handles all
database I/O operations. It ensures consistent connection handling, proper
resource cleanup, and transaction management.

Author: Warner (with AI assistance)
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional

from PledgePoints.models import PointEntry


class DatabaseManager:
    """
    Centralized database manager for pledge points operations.

    This class manages all database interactions, providing a clean interface
    for CRUD operations on point entries. It uses context managers to ensure
    proper connection handling and resource cleanup.

    Attributes:
        db_file (str): Path to the SQLite database file
    """

    def __init__(self, db_file: str):
        """
        Initialize the database manager.

        Args:
            db_file (str): Path to the SQLite database file
        """
        self.db_file = db_file
        self._ensure_initialized()

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.

        Yields a database connection and ensures it's properly closed
        after use. Handles commits and rollbacks automatically.

        Yields:
            sqlite3.Connection: Database connection object

        Example:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM Points")
        """
        conn = sqlite3.connect(self.db_file)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _ensure_initialized(self):
        """
        Ensure the database is initialized with the required schema.

        Creates the Points table if it doesn't exist and adds any missing
        columns to support the approval workflow.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Create the Points table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Time TEXT,
                    PointChange INTEGER,
                    Pledge TEXT,
                    Brother TEXT,
                    Comment TEXT,
                    approval_status TEXT DEFAULT 'pending',
                    approved_by TEXT,
                    approval_timestamp TEXT
                )
            """)

            # Add new columns to existing table if they don't exist
            # Note: SQLite doesn't support "ADD COLUMN IF NOT EXISTS"
            # so we need to handle errors for existing columns
            for column_def in [
                "approval_status TEXT DEFAULT 'pending'",
                "approved_by TEXT",
                "approval_timestamp TEXT",
            ]:
                try:
                    cursor.execute(f"ALTER TABLE Points ADD COLUMN {column_def}")
                except sqlite3.OperationalError:
                    # Column already exists, continue
                    pass

    def add_point_entries(self, entries: List[PointEntry]) -> int:
        """
        Add multiple point entries to the database.

        All entries are added with 'pending' approval status by default.

        Args:
            entries (List[PointEntry]): List of point entries to add

        Returns:
            int: Number of entries added
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Convert entries to tuples for bulk insert
            values = [entry.to_tuple() for entry in entries]
            cursor.executemany(
                """INSERT INTO Points (Time, PointChange, Pledge, Brother, Comment, approval_status)
                   VALUES (?, ?, ?, ?, ?, 'pending')""",
                values,
            )
            return len(entries)

    def get_all_points(
        self, status_filter: Optional[List[str]] = None
    ) -> List[PointEntry]:
        """
        Retrieve point entries from the database.

        Args:
            status_filter (Optional[List[str]]): List of approval statuses to filter by.
                                                 If None, returns all entries.
                                                 Example: ['approved', 'pending']

        Returns:
            List[PointEntry]: List of point entries matching the filter
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if status_filter:
                # Build parameterized query with placeholders
                placeholders = ",".join("?" for _ in status_filter)
                query = f"""
                    SELECT id, Time, PointChange, Pledge, Brother, Comment,
                           approval_status, approved_by, approval_timestamp
                    FROM Points
                    WHERE approval_status IN ({placeholders})
                """
                cursor.execute(query, status_filter)
            else:
                cursor.execute("""
                    SELECT id, Time, PointChange, Pledge, Brother, Comment,
                           approval_status, approved_by, approval_timestamp
                    FROM Points
                """)

            rows = cursor.fetchall()
            # Convert rows to PointEntry objects, skipping any that fail to parse
            entries = []
            for row in rows:
                try:
                    entries.append(PointEntry.from_db_row(row))
                except (ValueError, TypeError):
                    # Skip rows that can't be converted
                    continue

            return entries

    def get_approved_points(self) -> List[PointEntry]:
        """
        Get only approved point entries.

        Returns:
            List[PointEntry]: List of approved point entries
        """
        return self.get_all_points(status_filter=["approved"])

    def get_pending_points(self) -> List[PointEntry]:
        """
        Get only pending point entries.

        Returns:
            List[PointEntry]: List of pending point entries
        """
        return self.get_all_points(status_filter=["pending"])

    def get_point_by_id(self, point_id: int) -> Optional[PointEntry]:
        """
        Retrieve a specific point entry by its ID.

        Args:
            point_id (int): The database ID of the point entry

        Returns:
            Optional[PointEntry]: The point entry if found, None otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, Time, PointChange, Pledge, Brother, Comment,
                       approval_status, approved_by, approval_timestamp
                FROM Points
                WHERE id = ?
            """,
                (point_id,),
            )

            row = cursor.fetchone()
            if row:
                try:
                    return PointEntry.from_db_row(row)
                except (ValueError, TypeError):
                    return None
            return None

    def approve_points(self, point_ids: List[int], approver: str) -> List[PointEntry]:
        """
        Approve specific point entries by their IDs.

        Args:
            point_ids (List[int]): List of point entry IDs to approve
            approver (str): Name of the person approving the points

        Returns:
            List[PointEntry]: List of approved point entries
        """
        if not point_ids:
            return []

        with self.get_connection() as conn:
            cursor = conn.cursor()
            current_time = datetime.now().isoformat()

            # Get the entries that will be approved
            placeholders = ",".join("?" for _ in point_ids)
            cursor.execute(
                f"""
                SELECT id, Time, PointChange, Pledge, Brother, Comment,
                       approval_status, approved_by, approval_timestamp
                FROM Points
                WHERE id IN ({placeholders}) AND approval_status = 'pending'
            """,
                point_ids,
            )

            rows = cursor.fetchall()
            approved_entries = []
            for row in rows:
                try:
                    approved_entries.append(PointEntry.from_db_row(row))
                except (ValueError, TypeError):
                    continue

            # Update approval status
            cursor.execute(
                f"""
                UPDATE Points
                SET approval_status = 'approved',
                    approved_by = ?,
                    approval_timestamp = ?
                WHERE id IN ({placeholders}) AND approval_status = 'pending'
            """,
                [approver, current_time] + point_ids,
            )

            return approved_entries

    def approve_all_pending(self, approver: str) -> List[PointEntry]:
        """
        Approve all pending point entries.

        Args:
            approver (str): Name of the person approving the points

        Returns:
            List[PointEntry]: List of all approved point entries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            current_time = datetime.now().isoformat()

            # Get all pending entries
            cursor.execute("""
                SELECT id, Time, PointChange, Pledge, Brother, Comment,
                       approval_status, approved_by, approval_timestamp
                FROM Points
                WHERE approval_status = 'pending'
            """)

            rows = cursor.fetchall()
            approved_entries = []
            for row in rows:
                try:
                    approved_entries.append(PointEntry.from_db_row(row))
                except (ValueError, TypeError):
                    continue

            if not approved_entries:
                return []

            # Update all pending to approved
            cursor.execute(
                """
                UPDATE Points
                SET approval_status = 'approved',
                    approved_by = ?,
                    approval_timestamp = ?
                WHERE approval_status = 'pending'
            """,
                (approver, current_time),
            )

            return approved_entries

    def reject_points(self, point_ids: List[int], rejector: str) -> List[PointEntry]:
        """
        Reject specific point entries by their IDs.

        Args:
            point_ids (List[int]): List of point entry IDs to reject
            rejector (str): Name of the person rejecting the points

        Returns:
            List[PointEntry]: List of rejected point entries
        """
        if not point_ids:
            return []

        with self.get_connection() as conn:
            cursor = conn.cursor()
            current_time = datetime.now().isoformat()

            # Get the entries that will be rejected
            placeholders = ",".join("?" for _ in point_ids)
            cursor.execute(
                f"""
                SELECT id, Time, PointChange, Pledge, Brother, Comment,
                       approval_status, approved_by, approval_timestamp
                FROM Points
                WHERE id IN ({placeholders}) AND approval_status = 'pending'
            """,
                point_ids,
            )

            rows = cursor.fetchall()
            rejected_entries = []
            for row in rows:
                try:
                    rejected_entries.append(PointEntry.from_db_row(row))
                except (ValueError, TypeError):
                    continue

            # Update approval status
            cursor.execute(
                f"""
                UPDATE Points
                SET approval_status = 'rejected',
                    approved_by = ?,
                    approval_timestamp = ?
                WHERE id IN ({placeholders}) AND approval_status = 'pending'
            """,
                [rejector, current_time] + point_ids,
            )

            return rejected_entries

    def reject_all_pending(self, rejector: str) -> List[PointEntry]:
        """
        Reject all pending point entries.

        Args:
            rejector (str): Name of the person rejecting the points

        Returns:
            List[PointEntry]: List of all rejected point entries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            current_time = datetime.now().isoformat()

            # Get all pending entries
            cursor.execute("""
                           SELECT id,
                                  Time,
                                  PointChange,
                                  Pledge,
                                  Brother,
                                  Comment,
                                  approval_status,
                                  approved_by,
                                  approval_timestamp
                           FROM Points
                           WHERE approval_status = 'pending'
                           """)

            rows = cursor.fetchall()
            rejected_entries = []
            for row in rows:
                try:
                    rejected_entries.append(PointEntry.from_db_row(row))
                except (ValueError, TypeError):
                    continue

            if not rejected_entries:
                return []

            # Update all pending to rejected
            cursor.execute(
                """
                           UPDATE Points
                           SET approval_status    = 'rejected',
                               approved_by        = ?,
                               approval_timestamp = ?
                           WHERE approval_status = 'pending'
                           """,
                (rejector, current_time),
            )

            return rejected_entries
