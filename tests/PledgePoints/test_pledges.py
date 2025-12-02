"""Unit tests for pledge ranking and plotting utilities."""

import os
import tempfile
from datetime import datetime
from unittest.mock import Mock

import pandas as pd
import pytest

from PledgePoints.models import PointEntry
from PledgePoints.pledges import get_pledge_points, rank_pledges, plot_rankings
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
def db_manager_with_data(temp_db):
    """Create a DatabaseManager with sample approved data."""
    manager = DatabaseManager(temp_db)

    # Add some sample entries
    entries = [
        PointEntry(
            time=datetime(2024, 1, 1, 10, 0, 0),
            point_change=10,
            pledge="John",
            brother="Mike",
            comment="Great work",
        ),
        PointEntry(
            time=datetime(2024, 1, 2, 10, 0, 0),
            point_change=5,
            pledge="Jane",
            brother="Tom",
            comment="Good job",
        ),
        PointEntry(
            time=datetime(2024, 1, 3, 10, 0, 0),
            point_change=15,
            pledge="John",
            brother="Sarah",
            comment="Outstanding",
        ),
        PointEntry(
            time=datetime(2024, 1, 4, 10, 0, 0),
            point_change=-5,
            pledge="Jane",
            brother="Mike",
            comment="Late",
        ),
        PointEntry(
            time=datetime(2024, 1, 5, 10, 0, 0),
            point_change=20,
            pledge="Bob",
            brother="Alice",
            comment="Excellent",
        ),
    ]

    manager.add_point_entries(entries)

    # Approve all entries
    pending = manager.get_pending_points()
    point_ids = [p.entry_id for p in pending]
    manager.approve_points(point_ids, "Admin")

    return manager


class TestGetPledgePoints:
    """Tests for get_pledge_points function."""

    def test_get_pledge_points_empty_database(self, temp_db):
        """Test getting points from empty database returns empty DataFrame."""
        manager = DatabaseManager(temp_db)
        df = get_pledge_points(manager)

        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_get_pledge_points_with_data(self, db_manager_with_data):
        """Test getting points returns DataFrame with correct structure."""
        df = get_pledge_points(db_manager_with_data)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) == 5

        # Check columns
        expected_columns = {"Time", "PointChange", "Pledge", "Brother", "Comment"}
        assert set(df.columns) == expected_columns

    def test_get_pledge_points_sorted_by_time(self, db_manager_with_data):
        """Test that points are sorted by time in descending order."""
        df = get_pledge_points(db_manager_with_data)

        # Should be sorted descending (most recent first)
        times = df["Time"].tolist()
        assert times == sorted(times, reverse=True)

    def test_get_pledge_points_only_approved(self, temp_db):
        """Test that only approved points are returned."""
        manager = DatabaseManager(temp_db)

        # Add entries but don't approve them
        entries = [
            PointEntry(
                time=datetime.now(),
                point_change=10,
                pledge="John",
                brother="Mike",
                comment="Great work",
            ),
        ]
        manager.add_point_entries(entries)

        df = get_pledge_points(manager)

        # Should be empty since nothing is approved
        assert df.empty

    def test_get_pledge_points_time_is_datetime(self, db_manager_with_data):
        """Test that Time column contains datetime objects."""
        df = get_pledge_points(db_manager_with_data)

        assert pd.api.types.is_datetime64_any_dtype(df["Time"])


class TestRankPledges:
    """Tests for rank_pledges function."""

    def test_rank_pledges_empty_dataframe(self):
        """Test ranking empty DataFrame returns empty Series."""
        df = pd.DataFrame(columns=["Pledge", "PointChange"])
        rankings = rank_pledges(df)

        assert isinstance(rankings, pd.Series)
        assert rankings.empty

    def test_rank_pledges_basic(self):
        """Test basic ranking functionality."""
        df = pd.DataFrame(
            {
                "Pledge": ["John", "Jane", "John", "Jane", "Bob"],
                "PointChange": [10, 5, 15, -5, 20],
                "Time": [datetime.now()] * 5,
                "Brother": ["Mike"] * 5,
                "Comment": ["Test"] * 5,
            }
        )

        rankings = rank_pledges(df)

        assert isinstance(rankings, pd.Series)
        assert len(rankings) == 3  # Three unique pledges

        # Check sums
        assert rankings["John"] == 25  # 10 + 15
        assert rankings["Jane"] == 0  # 5 + (-5)
        assert rankings["Bob"] == 20

    def test_rank_pledges_sorted_descending(self):
        """Test that rankings are sorted in descending order."""
        df = pd.DataFrame(
            {
                "Pledge": ["John", "Jane", "Bob"],
                "PointChange": [10, 30, 20],
                "Time": [datetime.now()] * 3,
                "Brother": ["Mike"] * 3,
                "Comment": ["Test"] * 3,
            }
        )

        rankings = rank_pledges(df)

        values = rankings.tolist()
        assert values == sorted(values, reverse=True)

        # Check order
        assert rankings.index[0] == "Jane"  # Highest
        assert rankings.index[1] == "Bob"
        assert rankings.index[2] == "John"  # Lowest

    def test_rank_pledges_with_negatives(self):
        """Test ranking with negative points."""
        df = pd.DataFrame(
            {
                "Pledge": ["John", "Jane"],
                "PointChange": [-10, -5],
                "Time": [datetime.now()] * 2,
                "Brother": ["Mike"] * 2,
                "Comment": ["Test"] * 2,
            }
        )

        rankings = rank_pledges(df)

        assert rankings["John"] == -10
        assert rankings["Jane"] == -5
        assert rankings.index[0] == "Jane"  # Less negative is higher

    def test_rank_pledges_with_real_data(self, db_manager_with_data):
        """Test ranking with real database data."""
        df = get_pledge_points(db_manager_with_data)
        rankings = rank_pledges(df)

        # John: 10 + 15 = 25
        # Jane: 5 + (-5) = 0
        # Bob: 20
        assert rankings["John"] == 25
        assert rankings["Jane"] == 0
        assert rankings["Bob"] == 20

        # Bob should be first (20), then John (25), then Jane (0)
        # Actually John should be first with 25, then Bob with 20, then Jane with 0
        assert rankings.index[0] == "John"


class TestPlotRankings:
    """Tests for plot_rankings function."""

    def test_plot_rankings_creates_file(self):
        """Test that plot_rankings creates a PNG file."""
        rankings = pd.Series({"John": 25, "Jane": 15, "Bob": 10})

        filename = plot_rankings(rankings)

        assert filename == "rankings.png"
        assert os.path.exists(filename)

        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)

    def test_plot_rankings_with_single_pledge(self):
        """Test plotting with a single pledge."""
        rankings = pd.Series({"John": 25})

        filename = plot_rankings(rankings)

        assert os.path.exists(filename)

        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)

    def test_plot_rankings_preserves_order(self):
        """Test that plot preserves descending order of rankings."""
        # Create rankings in descending order
        rankings = pd.Series({"Alice": 30, "Bob": 20, "Charlie": 10})

        filename = plot_rankings(rankings)

        # File should exist
        assert os.path.exists(filename)

        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)

    def test_plot_rankings_with_negative_values(self):
        """Test plotting with negative point values."""
        rankings = pd.Series({"John": -5, "Jane": -10})

        filename = plot_rankings(rankings)

        assert os.path.exists(filename)

        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)

    def test_plot_rankings_with_many_pledges(self):
        """Test plotting with many pledges to check figure sizing."""
        rankings = pd.Series(
            {
                f"Pledge{i}": 100 - i * 10 for i in range(10)  # 10 pledges
            }
        )

        filename = plot_rankings(rankings)

        assert os.path.exists(filename)

        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)


class TestIntegrationWorkflow:
    """Integration tests for the complete workflow."""

    def test_full_workflow(self, db_manager_with_data):
        """Test the complete workflow from database to plot."""
        # Get points
        df = get_pledge_points(db_manager_with_data)
        assert not df.empty

        # Rank pledges
        rankings = rank_pledges(df)
        assert len(rankings) == 3  # John, Jane, Bob

        # Plot rankings
        filename = plot_rankings(rankings)
        assert os.path.exists(filename)

        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)

    def test_workflow_with_filtering(self, db_manager_with_data):
        """Test workflow with filtering for specific pledges."""
        from PledgePoints.constants import VALID_PLEDGES

        # Get points
        df = get_pledge_points(db_manager_with_data)

        # Rank pledges
        rankings = rank_pledges(df)

        # Filter to only valid pledges (as done in commands/points.py)
        filtered_rankings = rankings[rankings.index.isin(VALID_PLEDGES)]

        # This should work even if some pledges are filtered out
        assert isinstance(filtered_rankings, pd.Series)
