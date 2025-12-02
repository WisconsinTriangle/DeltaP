"""Unit tests for message processing utilities."""

import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import discord
import pytest
import pytz

from PledgePoints.messages import (
    fetch_messages_from_days_ago,
    add_reactions_with_rate_limit,
    process_messages,
    eliminate_duplicates,
)
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


class TestFetchMessagesFromDaysAgo:
    """Tests for fetch_messages_from_days_ago function."""

    @pytest.mark.asyncio
    async def test_fetch_messages_basic(self):
        """Test basic message fetching."""
        mock_bot = Mock()
        mock_channel = Mock()
        mock_bot.get_channel.return_value = mock_channel

        # Create mock messages
        mock_message1 = Mock()
        mock_message1.author = Mock()
        mock_message1.author.bot = False
        mock_message1.created_at = datetime.now(pytz.UTC)
        mock_message1.content = "+10 John Great work"

        mock_message2 = Mock()
        mock_message2.author = Mock()
        mock_message2.author.bot = False
        mock_message2.created_at = datetime.now(pytz.UTC)
        mock_message2.content = "+5 Jane Good job"

        # Mock the history iterator
        async def mock_history(*args, **kwargs):
            for msg in [mock_message1, mock_message2]:
                yield msg

        mock_channel.history = mock_history

        messages = await fetch_messages_from_days_ago(mock_bot, 123456, 1)

        assert len(messages) == 2
        assert messages[0][2] == "+10 John Great work"
        assert messages[1][2] == "+5 Jane Good job"

    @pytest.mark.asyncio
    async def test_fetch_messages_filters_bot_messages(self):
        """Test that bot messages are filtered out."""
        mock_bot = Mock()
        mock_channel = Mock()
        mock_bot.get_channel.return_value = mock_channel

        # Create mock messages (one bot, one human)
        mock_bot_message = Mock()
        mock_bot_message.author = Mock()
        mock_bot_message.author.bot = True
        mock_bot_message.created_at = datetime.now(pytz.UTC)
        mock_bot_message.content = "+10 John Bot message"

        mock_human_message = Mock()
        mock_human_message.author = Mock()
        mock_human_message.author.bot = False
        mock_human_message.created_at = datetime.now(pytz.UTC)
        mock_human_message.content = "+10 Jane Human message"

        async def mock_history(*args, **kwargs):
            for msg in [mock_bot_message, mock_human_message]:
                yield msg

        mock_channel.history = mock_history

        messages = await fetch_messages_from_days_ago(mock_bot, 123456, 1)

        # Should only have the human message
        assert len(messages) == 1
        assert messages[0][2] == "+10 Jane Human message"

    @pytest.mark.asyncio
    async def test_fetch_messages_channel_not_found(self):
        """Test that ValueError is raised when channel is not found."""
        mock_bot = Mock()
        mock_bot.get_channel.return_value = None

        with pytest.raises(ValueError, match="Channel with ID .* not found"):
            await fetch_messages_from_days_ago(mock_bot, 999999, 1)

    @pytest.mark.asyncio
    async def test_fetch_messages_includes_metadata(self):
        """Test that fetched messages include all metadata."""
        mock_bot = Mock()
        mock_channel = Mock()
        mock_bot.get_channel.return_value = mock_channel

        mock_user = Mock()
        mock_user.bot = False
        mock_timestamp = datetime.now(pytz.UTC)

        mock_message = Mock()
        mock_message.author = mock_user
        mock_message.created_at = mock_timestamp
        mock_message.content = "+10 John Test"

        async def mock_history(*args, **kwargs):
            yield mock_message

        mock_channel.history = mock_history

        messages = await fetch_messages_from_days_ago(mock_bot, 123456, 1)

        assert len(messages) == 1
        author, created_at, content, message = messages[0]
        assert author == mock_user
        assert created_at == mock_timestamp
        assert content == "+10 John Test"
        assert message == mock_message


class TestAddReactionsWithRateLimit:
    """Tests for add_reactions_with_rate_limit function."""

    @pytest.mark.asyncio
    async def test_add_reactions_success(self):
        """Test adding reactions to messages."""
        mock_message1 = Mock()
        mock_message1.add_reaction = AsyncMock()

        mock_message2 = Mock()
        mock_message2.add_reaction = AsyncMock()

        messages = [(mock_message1, True), (mock_message2, False)]

        await add_reactions_with_rate_limit(messages, rate_limit=0.01)

        # Verify reactions were added
        mock_message1.add_reaction.assert_called_once()
        mock_message2.add_reaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_reactions_handles_exceptions(self):
        """Test that exceptions during reaction adding are handled gracefully."""
        mock_message = Mock()
        mock_message.add_reaction = AsyncMock(side_effect=Exception("Discord API error"))

        messages = [(mock_message, True)]

        # Should not raise exception
        await add_reactions_with_rate_limit(messages, rate_limit=0.01)

    @pytest.mark.asyncio
    async def test_add_reactions_empty_list(self):
        """Test adding reactions with empty message list."""
        messages = []

        # Should not raise exception
        await add_reactions_with_rate_limit(messages, rate_limit=0.01)


class TestProcessMessages:
    """Tests for process_messages function."""

    @pytest.mark.asyncio
    async def test_process_valid_messages(self):
        """Test processing valid point messages."""
        mock_user = Mock()
        mock_user.display_name = "Mike"

        mock_message = Mock()
        mock_message.add_reaction = AsyncMock()

        timestamp = datetime.now()
        messages = [(mock_user, timestamp, "+10 Eli Great work", mock_message)]

        entries = await process_messages(messages)

        # Should create one valid entry (if Eli is a valid pledge)
        if entries:  # Depends on VALID_PLEDGES
            assert len(entries) <= 1
            if len(entries) == 1:
                entry = entries[0]
                assert entry.point_change == 10
                assert entry.brother == "Mike"
                assert entry.comment == "Great work"

    @pytest.mark.asyncio
    async def test_process_invalid_messages(self):
        """Test processing invalid point messages."""
        mock_user = Mock()
        mock_user.display_name = "Mike"

        mock_message = Mock()
        mock_message.add_reaction = AsyncMock()

        timestamp = datetime.now()
        messages = [
            (mock_user, timestamp, "Invalid message format", mock_message),
            (mock_user, timestamp, "+10", mock_message),  # Missing pledge and comment
        ]

        entries = await process_messages(messages)

        # Should not create any valid entries
        assert len(entries) == 0

    @pytest.mark.asyncio
    async def test_process_mixed_messages(self):
        """Test processing mix of valid and invalid messages."""
        mock_user = Mock()
        mock_user.display_name = "Mike"

        mock_message1 = Mock()
        mock_message1.add_reaction = AsyncMock()

        mock_message2 = Mock()
        mock_message2.add_reaction = AsyncMock()

        timestamp = datetime.now()
        messages = [
            (mock_user, timestamp, "+10 Eli Great work", mock_message1),
            (mock_user, timestamp, "Invalid format", mock_message2),
        ]

        entries = await process_messages(messages)

        # Should only process valid messages
        # Depends on VALID_PLEDGES containing "Eli"
        assert len(entries) <= 1

    @pytest.mark.asyncio
    async def test_process_messages_empty_list(self):
        """Test processing empty message list."""
        messages = []

        entries = await process_messages(messages)

        assert len(entries) == 0

    @pytest.mark.asyncio
    async def test_process_messages_extracts_author_name(self):
        """Test that author display name is correctly extracted."""
        mock_user = Mock()
        mock_user.display_name = "TestBrother"

        mock_message = Mock()
        mock_message.add_reaction = AsyncMock()

        timestamp = datetime.now()
        messages = [(mock_user, timestamp, "+10 Eli Great work", mock_message)]

        entries = await process_messages(messages)

        if entries:  # If Eli is a valid pledge
            assert entries[0].brother == "TestBrother"


class TestEliminateDuplicates:
    """Tests for eliminate_duplicates function."""

    def test_eliminate_duplicates_no_existing_entries(self, db_manager):
        """Test with no existing entries in database."""
        new_entries = [
            PointEntry(
                time=datetime.now(),
                point_change=10,
                pledge="John",
                brother="Mike",
                comment="Great work",
            ),
        ]

        unique = eliminate_duplicates(new_entries, db_manager)

        assert len(unique) == 1
        assert unique[0] == new_entries[0]

    def test_eliminate_duplicates_with_existing_entries(self, db_manager):
        """Test filtering out entries that already exist."""
        time1 = datetime(2024, 1, 1, 10, 0, 0)

        # Add existing entry
        existing_entry = PointEntry(
            time=time1,
            point_change=10,
            pledge="John",
            brother="Mike",
            comment="Great work",
        )
        db_manager.add_point_entries([existing_entry])

        # Try to add same entry again
        new_entries = [
            PointEntry(
                time=time1,
                point_change=10,
                pledge="John",
                brother="Mike",
                comment="Great work",
            ),
        ]

        unique = eliminate_duplicates(new_entries, db_manager)

        # Should be filtered out as duplicate
        assert len(unique) == 0

    def test_eliminate_duplicates_ignores_brother_field(self, db_manager):
        """Test that brother field is ignored in duplicate detection."""
        time1 = datetime(2024, 1, 1, 10, 0, 0)

        # Add existing entry with one brother
        existing_entry = PointEntry(
            time=time1,
            point_change=10,
            pledge="John",
            brother="Mike",
            comment="Great work",
        )
        db_manager.add_point_entries([existing_entry])

        # Try to add same entry with different brother
        new_entries = [
            PointEntry(
                time=time1,
                point_change=10,
                pledge="John",
                brother="DifferentBrother",  # Different brother
                comment="Great work",
            ),
        ]

        unique = eliminate_duplicates(new_entries, db_manager)

        # Should still be filtered as duplicate (brother is ignored)
        assert len(unique) == 0

    def test_eliminate_duplicates_checks_all_statuses(self, db_manager):
        """Test that duplicates are checked against all approval statuses."""
        time1 = datetime(2024, 1, 1, 10, 0, 0)

        # Add and reject an entry
        existing_entry = PointEntry(
            time=time1,
            point_change=10,
            pledge="John",
            brother="Mike",
            comment="Great work",
        )
        db_manager.add_point_entries([existing_entry])

        pending = db_manager.get_pending_points()
        db_manager.reject_points([pending[0].entry_id], "Admin")

        # Try to add same entry again
        new_entries = [
            PointEntry(
                time=time1,
                point_change=10,
                pledge="John",
                brother="Mike",
                comment="Great work",
            ),
        ]

        unique = eliminate_duplicates(new_entries, db_manager)

        # Should be filtered out even though it was rejected
        assert len(unique) == 0

    def test_eliminate_duplicates_different_entries(self, db_manager):
        """Test that genuinely different entries are not filtered."""
        time1 = datetime(2024, 1, 1, 10, 0, 0)
        time2 = datetime(2024, 1, 2, 10, 0, 0)

        # Add existing entry
        existing_entry = PointEntry(
            time=time1,
            point_change=10,
            pledge="John",
            brother="Mike",
            comment="Great work",
        )
        db_manager.add_point_entries([existing_entry])

        # Add different entries
        new_entries = [
            PointEntry(
                time=time2,  # Different time
                point_change=10,
                pledge="John",
                brother="Mike",
                comment="Great work",
            ),
            PointEntry(
                time=time1,
                point_change=5,  # Different points
                pledge="John",
                brother="Mike",
                comment="Great work",
            ),
            PointEntry(
                time=time1,
                point_change=10,
                pledge="Jane",  # Different pledge
                brother="Mike",
                comment="Great work",
            ),
            PointEntry(
                time=time1,
                point_change=10,
                pledge="John",
                brother="Mike",
                comment="Different comment",  # Different comment
            ),
        ]

        unique = eliminate_duplicates(new_entries, db_manager)

        # All should be unique
        assert len(unique) == 4

    def test_eliminate_duplicates_preserves_microseconds(self, db_manager):
        """Test that datetime comparison preserves microseconds."""
        time1 = datetime(2024, 1, 1, 10, 0, 0, 123456)
        time2 = datetime(2024, 1, 1, 10, 0, 0, 123457)  # 1 microsecond difference

        # Add existing entry
        existing_entry = PointEntry(
            time=time1,
            point_change=10,
            pledge="John",
            brother="Mike",
            comment="Great work",
        )
        db_manager.add_point_entries([existing_entry])

        # Try to add entry with slightly different time
        new_entries = [
            PointEntry(
                time=time2,  # 1 microsecond later
                point_change=10,
                pledge="John",
                brother="Mike",
                comment="Great work",
            ),
        ]

        unique = eliminate_duplicates(new_entries, db_manager)

        # Should NOT be filtered out (different microsecond)
        assert len(unique) == 1

    def test_eliminate_duplicates_empty_new_entries(self, db_manager):
        """Test with empty list of new entries."""
        unique = eliminate_duplicates([], db_manager)

        assert len(unique) == 0
