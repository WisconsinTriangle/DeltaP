"""Unit tests for study_hours command."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from commands.points import setup


class TestStudyHoursCommand:
    """Tests for study_hours command."""

    @pytest.mark.asyncio
    async def test_study_hours_command_exists(self, sample_env_vars):
        """Test that study_hours command is registered."""
        mock_bot = Mock()
        mock_bot.tree = Mock()
        commands_registered = []

        def mock_command(*args, **kwargs):
            def decorator(func):
                commands_registered.append((kwargs.get('name'), func))
                return func
            return decorator

        mock_bot.tree.command = mock_command

        # Need to mock the DatabaseManager
        with patch('commands.points.DatabaseManager'):
            setup(mock_bot)

        # Check study_hours command was registered
        command_names = [name for name, _ in commands_registered]
        assert 'study_hours' in command_names

    @pytest.mark.asyncio
    async def test_study_hours_invalid_pledge_name(self, sample_env_vars):
        """Test study_hours with invalid pledge name."""
        mock_bot = Mock()
        mock_bot.tree = Mock()
        study_hours_func = None

        def mock_command(*args, **kwargs):
            def decorator(func):
                nonlocal study_hours_func
                if kwargs.get('name') == 'study_hours':
                    study_hours_func = func
                return func
            return decorator

        mock_bot.tree.command = mock_command

        with patch('commands.points.DatabaseManager'):
            setup(mock_bot)

        # Create mock interaction
        mock_interaction = Mock()
        mock_interaction.response = Mock()
        mock_interaction.response.send_message = AsyncMock()

        # Test with invalid pledge name
        if study_hours_func:
            await study_hours_func(mock_interaction, "InvalidPledge", 5)
            mock_interaction.response.send_message.assert_called_once()
            # Check that the message contains invalid pledge error
            call_args = mock_interaction.response.send_message.call_args
            assert "invalid" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_study_hours_negative_hours(self, sample_env_vars):
        """Test study_hours with negative hours."""
        mock_bot = Mock()
        mock_bot.tree = Mock()
        study_hours_func = None

        def mock_command(*args, **kwargs):
            def decorator(func):
                nonlocal study_hours_func
                if kwargs.get('name') == 'study_hours':
                    study_hours_func = func
                return func
            return decorator

        mock_bot.tree.command = mock_command

        with patch('commands.points.DatabaseManager'):
            setup(mock_bot)

        # Create mock interaction
        mock_interaction = Mock()
        mock_interaction.response = Mock()
        mock_interaction.response.send_message = AsyncMock()

        # Test with negative hours
        if study_hours_func:
            await study_hours_func(mock_interaction, "Eli", -5)
            mock_interaction.response.send_message.assert_called_once()
            # Check that the message contains negative hours error
            call_args = mock_interaction.response.send_message.call_args
            assert "negative" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_study_hours_successful_submission(self, sample_env_vars):
        """Test successful study hours submission."""
        mock_bot = Mock()
        mock_bot.tree = Mock()
        study_hours_func = None

        def mock_command(*args, **kwargs):
            def decorator(func):
                nonlocal study_hours_func
                if kwargs.get('name') == 'study_hours':
                    study_hours_func = func
                return func
            return decorator

        mock_bot.tree.command = mock_command

        # Mock the DatabaseManager
        mock_db_manager = Mock()
        mock_db_manager.add_point_entries = Mock(return_value=1)

        with patch('commands.points.DatabaseManager', return_value=mock_db_manager):
            setup(mock_bot)

        # Create mock interaction
        mock_interaction = Mock()
        mock_interaction.response = Mock()
        mock_interaction.response.send_message = AsyncMock()

        # Test successful submission
        if study_hours_func:
            await study_hours_func(mock_interaction, "Eli", 5)
            
            # Verify the database manager was called
            mock_db_manager.add_point_entries.assert_called_once()
            
            # Verify the response was sent
            mock_interaction.response.send_message.assert_called_once()
            
            # Check the response message
            call_args = mock_interaction.response.send_message.call_args
            message = call_args[0][0]
            assert "Eli" in message
            assert "5" in message
            assert "pending" in message.lower() or "approval" in message.lower()
            assert "Study" in message
