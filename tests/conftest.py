"""Pytest configuration and fixtures for the test suite."""

import os
import sys
from pathlib import Path

import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_env_vars(monkeypatch):
    """Fixture to set up test environment variables."""
    monkeypatch.setenv("DISCORD_TOKEN", "test_token_123")
    monkeypatch.setenv("CSV_NAME", "test_pledge_points.db")
    monkeypatch.setenv("CHANNEL_ID", "123456789")


@pytest.fixture
def mock_discord_interaction():
    """Fixture to create a mock Discord interaction."""
    from unittest.mock import AsyncMock, Mock

    interaction = Mock()
    interaction.response = Mock()
    interaction.response.send_message = AsyncMock()
    interaction.followup = Mock()
    interaction.followup.send = AsyncMock()
    interaction.edit_original_response = AsyncMock()
    interaction.user = Mock()
    interaction.user.name = "TestUser"
    interaction.user.id = 123456789

    return interaction
