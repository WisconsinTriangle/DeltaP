"""Unit tests for admin commands."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from commands.admin import setup


class TestAdminCommandSetup:
    """Tests for admin command setup."""

    @pytest.mark.asyncio
    async def test_ping_command_exists(self):
        """Test that ping command is registered."""
        mock_bot = Mock()
        mock_bot.tree = Mock()
        commands_registered = []

        def mock_command(*args, **kwargs):
            def decorator(func):
                commands_registered.append((kwargs.get("name"), func))
                return func

            return decorator

        mock_bot.tree.command = mock_command
        mock_bot.latency = 0.05

        setup(mock_bot)

        # Check ping command was registered
        command_names = [name for name, _ in commands_registered]
        assert "ping" in command_names

    @pytest.mark.asyncio
    async def test_shutdown_command_exists(self):
        """Test that shutdown command is registered."""
        mock_bot = Mock()
        mock_bot.tree = Mock()
        commands_registered = []

        def mock_command(*args, **kwargs):
            def decorator(func):
                commands_registered.append((kwargs.get("name"), func))
                return func

            return decorator

        mock_bot.tree.command = mock_command
        mock_bot.close = AsyncMock()

        setup(mock_bot)

        # Check shutdown command was registered
        command_names = [name for name, _ in commands_registered]
        assert "shutdown" in command_names


class TestShutdownPermissions:
    """Tests for shutdown command permissions."""

    @pytest.mark.asyncio
    async def test_shutdown_checks_role(self):
        """Test that shutdown command checks for appropriate role."""
        mock_bot = Mock()
        mock_bot.tree = Mock()
        mock_bot.close = AsyncMock()
        shutdown_func = None

        def mock_command(*args, **kwargs):
            def decorator(func):
                nonlocal shutdown_func
                if kwargs.get("name") == "shutdown":
                    shutdown_func = func
                return func

            return decorator

        mock_bot.tree.command = mock_command
        setup(mock_bot)

        # Create mock interaction
        mock_interaction = Mock()
        mock_interaction.response = Mock()
        mock_interaction.response.send_message = AsyncMock()

        # Test with check_info_systems_role returning False
        with patch(
            "commands.admin.check_info_systems_role", new_callable=AsyncMock
        ) as mock_role_check:
            mock_role_check.return_value = False

            if shutdown_func:
                await shutdown_func(mock_interaction)
                mock_interaction.response.send_message.assert_called_once()
                mock_bot.close.assert_not_called()
