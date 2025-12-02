"""Unit tests for Discord helper utilities."""

from datetime import datetime

import pytest
from unittest.mock import AsyncMock, Mock

from utils.discord_helpers import (
    format_approval_status,
    format_approval_confirmation,
    format_pending_points_list,
    format_point_entry_detailed,
    format_point_entry_summary,
    format_rankings_text,
    send_chunked_message,
)
from PledgePoints.models import PointEntry


class TestSendChunkedMessage:
    """Tests for send_chunked_message function."""

    @pytest.mark.asyncio
    async def test_short_message_single_send(self, mock_discord_interaction):
        """Test that short messages are sent as a single message."""
        short_message = "This is a short message"

        await send_chunked_message(mock_discord_interaction, short_message)

        mock_discord_interaction.followup.send.assert_called_once_with(short_message)

    @pytest.mark.asyncio
    async def test_long_message_chunked(self, mock_discord_interaction):
        """Test that long messages are split into chunks."""
        long_message = "A" * 2500  # Exceeds default chunk size of 1900

        await send_chunked_message(
            mock_discord_interaction, long_message, chunk_size=1000
        )

        # Should be called 3 times (2500 chars / 1000 chunk_size = 3 chunks)
        assert mock_discord_interaction.followup.send.call_count == 3


class TestFormatApprovalStatus:
    """Tests for format_approval_status function."""

    def test_approved_status(self):
        """Test formatting of approved status."""
        entry = PointEntry(
            entry_id=1,
            time=datetime.now(),
            brother="John",
            point_change=10,
            pledge="Jake",
            comment="Great work",
            approval_status="approved",
            approved_by="Admin",
            approval_timestamp=datetime(2025, 1, 1, 12, 0, 0),
        )

        result = format_approval_status(entry)

        assert "✅" in result
        assert "Approved" in result
        assert "Admin" in result
        assert "2025-01-01" in result

    def test_rejected_status(self):
        """Test formatting of rejected status."""
        entry = PointEntry(
            entry_id=1,
            time=datetime.now(),
            brother="John",
            point_change=10,
            pledge="Jake",
            comment="Great work",
            approval_status="rejected",
            approved_by="Admin",
            approval_timestamp=datetime(2025, 1, 1, 12, 0, 0),
        )

        result = format_approval_status(entry)

        assert "❌" in result
        assert "Rejected" in result
        assert "Admin" in result

    def test_pending_status(self):
        """Test formatting of pending status."""
        entry = PointEntry(
            entry_id=1,
            time=datetime.now(),
            brother="John",
            point_change=10,
            pledge="Jake",
            comment="Great work",
            approval_status="pending",
        )

        result = format_approval_status(entry)

        assert "⏳" in result
        assert "Pending" in result


class TestFormatPointEntrySummary:
    """Tests for format_point_entry_summary function."""

    def test_summary_formatting(self):
        """Test basic summary formatting."""
        entry = PointEntry(
            entry_id=42,
            time=datetime.now(),
            brother="John",
            point_change=10,
            pledge="Jake",
            comment="Great work",
        )

        result = format_point_entry_summary(entry)

        assert "ID 42" in result
        assert "John" in result
        assert "Jake" in result
        assert "+10" in result


class TestFormatPointEntryDetailed:
    """Tests for format_point_entry_detailed function."""

    def test_detailed_formatting(self):
        """Test detailed entry formatting."""
        entry = PointEntry(
            entry_id=42,
            time=datetime(2025, 1, 1, 12, 0, 0),
            brother="John",
            point_change=10,
            pledge="Jake",
            comment="Great work",
            approval_status="approved",
            approved_by="Admin",
        )

        result = format_point_entry_detailed(entry)

        assert "ID: 42" in result
        assert "John" in result
        assert "Jake" in result
        assert "+10" in result
        assert "Great work" in result
        assert "2025-01-01" in result


class TestFormatRankingsText:
    """Tests for format_rankings_text function."""

    def test_empty_rankings(self):
        """Test handling of empty rankings."""
        result = format_rankings_text([])

        assert "No rankings data available" in result

    def test_rankings_with_medals(self):
        """Test that top 3 get medal emojis."""
        rankings = [
            ("Jake", 100),
            ("John", 80),
            ("Mike", 60),
            ("Tom", 40),
        ]

        result = format_rankings_text(rankings)

        assert "🥇" in result  # 1st place
        assert "🥈" in result  # 2nd place
        assert "🥉" in result  # 3rd place
        assert "4." in result  # 4th place numbered
        assert "Jake" in result
        assert "100" in result


class TestFormatPendingPointsList:
    """Tests for format_pending_points_list function."""

    def test_empty_pending_list(self):
        """Test handling of empty pending points."""
        result = format_pending_points_list([])

        assert "No pending points found" in result

    def test_pending_list_formatting(self):
        """Test formatting of pending points list."""
        entries = [
            PointEntry(
                entry_id=1,
                time=datetime.now(),
                brother="John",
                point_change=10,
                pledge="Jake",
                comment="Good",
                approval_status="pending",
            ),
        ]

        result = format_pending_points_list(entries)

        assert "Pending Point Submissions" in result
        assert "ID: 1" in result


class TestFormatApprovalConfirmation:
    """Tests for format_approval_confirmation function."""

    def test_approval_confirmation(self):
        """Test approval confirmation message."""
        entries = [
            PointEntry(
                entry_id=1,
                time=datetime.now(),
                brother="John",
                point_change=10,
                pledge="Jake",
                comment="Good",
            ),
        ]

        result = format_approval_confirmation(entries, approved=True)

        assert "✅" in result
        assert "Approved" in result
        assert "1 point submission" in result

    def test_rejection_confirmation(self):
        """Test rejection confirmation message."""
        entries = [
            PointEntry(
                entry_id=1,
                time=datetime.now(),
                brother="John",
                point_change=10,
                pledge="Jake",
                comment="Good",
            ),
        ]

        result = format_approval_confirmation(entries, approved=False)

        assert "❌" in result
        assert "Rejected" in result
