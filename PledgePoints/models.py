"""
Data models for the pledge points system.

This module defines dataclasses that represent the core data structures
used throughout the application, replacing raw tuples with type-safe objects.

Author: Warner (with AI assistance)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PointEntry:
    """
    Represents a single point entry in the pledge points system.

    This dataclass encapsulates all information about a point transaction,
    including the time it occurred, the point change, which pledge and brother
    were involved, and any associated comment.

    Attributes:
        time (datetime): When the point entry was created
        point_change (int): The number of points (positive or negative)
        pledge (str): Name of the pledge receiving points
        brother (str): Name of the brother who awarded the points
        comment (str): Description or reason for the point change
        entry_id (Optional[int]): Database ID (None for new entries)
        approval_status (str): Current approval status ('pending', 'approved', 'rejected')
        approved_by (Optional[str]): Name of person who approved/rejected
        approval_timestamp (Optional[datetime]): When the approval/rejection occurred
    """

    time: datetime
    point_change: int
    pledge: str
    brother: str
    comment: str
    entry_id: Optional[int] = None
    approval_status: str = "pending"
    approved_by: Optional[str] = None
    approval_timestamp: Optional[datetime] = None

    def to_tuple(self) -> tuple:
        """
        Convert to tuple format for database operations.

        Returns:
            tuple: (time, point_change, pledge, brother, comment)
        """
        return (self.time, self.point_change, self.pledge, self.brother, self.comment)

    @classmethod
    def from_db_row(cls, row: tuple) -> "PointEntry":
        """
        Create a PointEntry from a database row.

        Args:
            row (tuple): Database row with columns in order:
                        (id, Time, PointChange, Pledge, Brother, Comment,
                         approval_status, approved_by, approval_timestamp)

        Returns:
            PointEntry: New PointEntry instance
        """
        (
            entry_id,
            time_str,
            point_change,
            pledge,
            brother,
            comment,
            approval_status,
            approved_by,
            approval_timestamp_str,
        ) = row

        # Convert time string to datetime
        if isinstance(time_str, datetime):
            time_dt = time_str
        else:
            time_dt = datetime.fromisoformat(time_str)

        # Convert approval timestamp if present
        approval_dt = None
        if approval_timestamp_str:
            if isinstance(approval_timestamp_str, datetime):
                approval_dt = approval_timestamp_str
            else:
                try:
                    approval_dt = datetime.fromisoformat(approval_timestamp_str)
                except (ValueError, TypeError):
                    pass

        return cls(
            time=time_dt,
            point_change=point_change,
            pledge=pledge,
            brother=brother,
            comment=comment,
            entry_id=entry_id,
            approval_status=approval_status or "pending",
            approved_by=approved_by,
            approval_timestamp=approval_dt,
        )

    @classmethod
    def from_simple_row(cls, row: tuple) -> "PointEntry":
        """
        Create a PointEntry from a simple database row (without approval fields).

        Args:
            row (tuple): Database row with columns: (Time, PointChange, Pledge, Brother, Comment)

        Returns:
            PointEntry: New PointEntry instance with default approval status
        """
        time_str, point_change, pledge, brother, comment = row

        # Convert time string to datetime
        if isinstance(time_str, datetime):
            time_dt = time_str
        else:
            time_dt = datetime.fromisoformat(time_str)

        return cls(
            time=time_dt,
            point_change=point_change,
            pledge=pledge,
            brother=brother,
            comment=comment,
        )
