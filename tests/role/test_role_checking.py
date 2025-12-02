"""Unit tests for role checking utilities."""

import pytest
from unittest.mock import Mock

from role.role_checking import (
    check_eboard_role,
    check_brother_role,
    check_info_systems_role,
)


@pytest.fixture
def mock_interaction():
    """Create a mock Discord interaction."""
    interaction = Mock()
    interaction.guild = Mock()
    interaction.user = Mock()
    interaction.user.roles = []
    return interaction


@pytest.fixture
def mock_eboard_role():
    """Create a mock Executive Board role."""
    role = Mock()
    role.name = "Executive Board"
    return role


@pytest.fixture
def mock_brother_role():
    """Create a mock Brother role."""
    role = Mock()
    role.name = "Brother"
    return role


@pytest.fixture
def mock_info_systems_role():
    """Create a mock Info Systems role."""
    role = Mock()
    role.id = 1032306248235888762
    role.name = "Info Systems"
    return role


class TestCheckEboardRole:
    """Tests for check_eboard_role function."""

    @pytest.mark.asyncio
    async def test_user_has_eboard_role(self, mock_interaction, mock_eboard_role):
        """Test that function returns True when user has Executive Board role."""
        mock_interaction.user.roles = [mock_eboard_role]
        mock_interaction.guild.roles = [mock_eboard_role]

        result = await check_eboard_role(mock_interaction)
        assert result is True

    @pytest.mark.asyncio
    async def test_user_without_eboard_role(self, mock_interaction):
        """Test that function returns False when user doesn't have Executive Board role."""
        other_role = Mock()
        other_role.name = "Member"
        mock_interaction.user.roles = [other_role]
        mock_interaction.guild.roles = [other_role]

        result = await check_eboard_role(mock_interaction)
        assert result is False

    @pytest.mark.asyncio
    async def test_eboard_role_does_not_exist(self, mock_interaction):
        """Test that function returns False when Executive Board role doesn't exist in guild."""
        mock_interaction.guild.roles = []

        result = await check_eboard_role(mock_interaction)
        assert result is False

    @pytest.mark.asyncio
    async def test_user_has_multiple_roles_including_eboard(
        self, mock_interaction, mock_eboard_role
    ):
        """Test that function returns True when user has multiple roles including Executive Board."""
        other_role = Mock()
        other_role.name = "Member"
        mock_interaction.user.roles = [other_role, mock_eboard_role]
        mock_interaction.guild.roles = [other_role, mock_eboard_role]

        result = await check_eboard_role(mock_interaction)
        assert result is True


class TestCheckBrotherRole:
    """Tests for check_brother_role function."""

    @pytest.mark.asyncio
    async def test_user_has_brother_role(self, mock_interaction, mock_brother_role):
        """Test that function returns True when user has Brother role."""
        mock_interaction.user.roles = [mock_brother_role]
        mock_interaction.guild.roles = [mock_brother_role]

        result = await check_brother_role(mock_interaction)
        assert result is True

    @pytest.mark.asyncio
    async def test_user_without_brother_role(self, mock_interaction):
        """Test that function returns False when user doesn't have Brother role."""
        other_role = Mock()
        other_role.name = "Guest"
        mock_interaction.user.roles = [other_role]
        mock_interaction.guild.roles = [other_role]

        result = await check_brother_role(mock_interaction)
        assert result is False

    @pytest.mark.asyncio
    async def test_brother_role_does_not_exist(self, mock_interaction):
        """Test that function returns False when Brother role doesn't exist in guild."""
        mock_interaction.guild.roles = []

        result = await check_brother_role(mock_interaction)
        assert result is False

    @pytest.mark.asyncio
    async def test_user_has_multiple_roles_including_brother(
        self, mock_interaction, mock_brother_role
    ):
        """Test that function returns True when user has multiple roles including Brother."""
        other_role = Mock()
        other_role.name = "Member"
        mock_interaction.user.roles = [other_role, mock_brother_role]
        mock_interaction.guild.roles = [other_role, mock_brother_role]

        result = await check_brother_role(mock_interaction)
        assert result is True


class TestCheckInfoSystemsRole:
    """Tests for check_info_systems_role function."""

    @pytest.mark.asyncio
    async def test_user_has_info_systems_role(
        self, mock_interaction, mock_info_systems_role
    ):
        """Test that function returns True when user has Info Systems role."""
        mock_interaction.user.roles = [mock_info_systems_role]
        mock_interaction.guild.roles = [mock_info_systems_role]

        result = await check_info_systems_role(mock_interaction)
        assert result is True

    @pytest.mark.asyncio
    async def test_user_without_info_systems_role(self, mock_interaction):
        """Test that function returns False when user doesn't have Info Systems role."""
        other_role = Mock()
        other_role.id = 999999999
        other_role.name = "Member"
        mock_interaction.user.roles = [other_role]
        mock_interaction.guild.roles = [other_role]

        result = await check_info_systems_role(mock_interaction)
        assert result is False

    @pytest.mark.asyncio
    async def test_info_systems_role_does_not_exist(self, mock_interaction):
        """Test that function returns False when Info Systems role doesn't exist in guild."""
        mock_interaction.guild.roles = []

        result = await check_info_systems_role(mock_interaction)
        assert result is False

    @pytest.mark.asyncio
    async def test_user_has_multiple_roles_including_info_systems(
        self, mock_interaction, mock_info_systems_role
    ):
        """Test that function returns True when user has multiple roles including Info Systems."""
        other_role = Mock()
        other_role.id = 999999999
        other_role.name = "Member"
        mock_interaction.user.roles = [other_role, mock_info_systems_role]
        mock_interaction.guild.roles = [other_role, mock_info_systems_role]

        result = await check_info_systems_role(mock_interaction)
        assert result is True

    @pytest.mark.asyncio
    async def test_role_with_wrong_id(self, mock_interaction):
        """Test that function returns False when role has wrong ID."""
        wrong_role = Mock()
        wrong_role.id = 123456789
        wrong_role.name = "Info Systems"
        mock_interaction.user.roles = [wrong_role]
        mock_interaction.guild.roles = [wrong_role]

        result = await check_info_systems_role(mock_interaction)
        assert result is False
