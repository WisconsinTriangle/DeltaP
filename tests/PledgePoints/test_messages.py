"""
Tests for message processing and duplicate elimination.

This module tests the message processing functions, particularly
focusing on the eliminate_duplicates function which was failing
to correctly identify duplicates due to datetime formatting issues.
"""

import tempfile
from datetime import datetime

import pytest
import pytz

from PledgePoints.messages import eliminate_duplicates
from PledgePoints.models import PointEntry
from PledgePoints.sqlutils import DatabaseManager


class TestEliminateDuplicates:
    """Tests for eliminate_duplicates function."""

    def test_eliminates_exact_duplicate_with_microseconds(self):
        """Test that entries with identical timestamps including microseconds are detected as duplicates."""
        # Create a timezone-aware datetime with microseconds (like Discord messages)
        timestamp = datetime(2025, 1, 15, 10, 30, 45, 123456, tzinfo=pytz.UTC)
        
        # Create test database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_manager = DatabaseManager(tmp_db.name)
            
            # Create an entry that's already in the database
            existing_entry = PointEntry(
                time=timestamp,
                point_change=10,
                pledge="John",
                brother="Alice",
                comment="Great work"
            )
            
            # Add it to the database
            db_manager.add_point_entries([existing_entry])
            
            # Create a new entry with the same data (duplicate)
            new_entry = PointEntry(
                time=timestamp,
                point_change=10,
                pledge="John",
                brother="Alice",
                comment="Great work"
            )
            
            # Run eliminate_duplicates
            unique_entries = eliminate_duplicates([new_entry], db_manager)
            
            # Should be empty since it's a duplicate
            assert len(unique_entries) == 0, "Duplicate entry should have been eliminated"

    def test_keeps_non_duplicate_entries(self):
        """Test that non-duplicate entries are preserved."""
        timestamp1 = datetime(2025, 1, 15, 10, 30, 45, 123456, tzinfo=pytz.UTC)
        timestamp2 = datetime(2025, 1, 15, 10, 30, 46, 789012, tzinfo=pytz.UTC)  # Different by 1 second
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_manager = DatabaseManager(tmp_db.name)
            
            # Add existing entry
            existing_entry = PointEntry(
                time=timestamp1,
                point_change=10,
                pledge="John",
                brother="Alice",
                comment="Great work"
            )
            db_manager.add_point_entries([existing_entry])
            
            # Create a new entry with different timestamp
            new_entry = PointEntry(
                time=timestamp2,
                point_change=10,
                pledge="John",
                brother="Alice",
                comment="Great work"
            )
            
            unique_entries = eliminate_duplicates([new_entry], db_manager)
            
            # Should keep the new entry since timestamp is different
            assert len(unique_entries) == 1
            assert unique_entries[0].time == timestamp2

    def test_different_fields_not_duplicates(self):
        """Test that entries with different fields are not considered duplicates."""
        timestamp = datetime(2025, 1, 15, 10, 30, 45, 123456, tzinfo=pytz.UTC)
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_manager = DatabaseManager(tmp_db.name)
            
            # Add existing entry
            existing_entry = PointEntry(
                time=timestamp,
                point_change=10,
                pledge="John",
                brother="Alice",
                comment="Great work"
            )
            db_manager.add_point_entries([existing_entry])
            
            # Test different point_change
            new_entry1 = PointEntry(
                time=timestamp,
                point_change=15,  # Different
                pledge="John",
                brother="Alice",
                comment="Great work"
            )
            
            # Test different pledge
            new_entry2 = PointEntry(
                time=timestamp,
                point_change=10,
                pledge="Jane",  # Different
                brother="Alice",
                comment="Great work"
            )
            
            # Test different brother
            new_entry3 = PointEntry(
                time=timestamp,
                point_change=10,
                pledge="John",
                brother="Bob",  # Different
                comment="Great work"
            )
            
            # Test different comment
            new_entry4 = PointEntry(
                time=timestamp,
                point_change=10,
                pledge="John",
                brother="Alice",
                comment="Excellent work"  # Different
            )
            
            unique_entries = eliminate_duplicates(
                [new_entry1, new_entry2, new_entry3, new_entry4], 
                db_manager
            )
            
            # All should be kept since they differ from existing entry
            assert len(unique_entries) == 4

    def test_handles_multiple_new_entries_with_duplicates(self):
        """Test handling multiple new entries where some are duplicates."""
        timestamp1 = datetime(2025, 1, 15, 10, 30, 45, 123456, tzinfo=pytz.UTC)
        timestamp2 = datetime(2025, 1, 15, 10, 31, 00, 654321, tzinfo=pytz.UTC)
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_manager = DatabaseManager(tmp_db.name)
            
            # Add existing entry
            existing_entry = PointEntry(
                time=timestamp1,
                point_change=10,
                pledge="John",
                brother="Alice",
                comment="Great work"
            )
            db_manager.add_point_entries([existing_entry])
            
            # Create new entries - one duplicate, one unique
            duplicate_entry = PointEntry(
                time=timestamp1,
                point_change=10,
                pledge="John",
                brother="Alice",
                comment="Great work"
            )
            
            unique_entry = PointEntry(
                time=timestamp2,
                point_change=5,
                pledge="Jane",
                brother="Bob",
                comment="Good job"
            )
            
            unique_entries = eliminate_duplicates(
                [duplicate_entry, unique_entry], 
                db_manager
            )
            
            # Should only keep the unique entry
            assert len(unique_entries) == 1
            assert unique_entries[0].time == timestamp2

    def test_handles_empty_database(self):
        """Test that all entries are kept when database is empty."""
        timestamp = datetime(2025, 1, 15, 10, 30, 45, 123456, tzinfo=pytz.UTC)
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_manager = DatabaseManager(tmp_db.name)
            
            # Don't add any entries to database
            
            # Create new entries
            new_entry = PointEntry(
                time=timestamp,
                point_change=10,
                pledge="John",
                brother="Alice",
                comment="Great work"
            )
            
            unique_entries = eliminate_duplicates([new_entry], db_manager)
            
            # Should keep all entries
            assert len(unique_entries) == 1

    def test_handles_empty_new_entries(self):
        """Test that function handles empty list of new entries."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_manager = DatabaseManager(tmp_db.name)
            
            unique_entries = eliminate_duplicates([], db_manager)
            
            # Should return empty list
            assert len(unique_entries) == 0

    def test_distinguishes_entries_with_different_microseconds(self):
        """Test that entries with same second but different microseconds are NOT duplicates.
        
        This is the critical bug fix: Discord messages can be posted within the same second
        but with different microseconds. These should be treated as separate entries.
        """
        # Two timestamps in the same second but different microseconds
        timestamp1 = datetime(2025, 1, 15, 10, 30, 45, 123456, tzinfo=pytz.UTC)
        timestamp2 = datetime(2025, 1, 15, 10, 30, 45, 654321, tzinfo=pytz.UTC)
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_manager = DatabaseManager(tmp_db.name)
            
            # Add first entry
            entry1 = PointEntry(
                time=timestamp1,
                point_change=10,
                pledge="John",
                brother="Alice",
                comment="Great work"
            )
            db_manager.add_point_entries([entry1])
            
            # Try to add second entry with different microseconds
            entry2 = PointEntry(
                time=timestamp2,
                point_change=10,
                pledge="John",
                brother="Alice",
                comment="Great work"
            )
            
            unique_entries = eliminate_duplicates([entry2], db_manager)
            
            # Should NOT be eliminated because microseconds are different
            assert len(unique_entries) == 1, (
                f"Entries with different microseconds should not be duplicates. "
                f"Entry 1: {timestamp1}, Entry 2: {timestamp2}"
            )
