"""Unit tests for configuration settings."""

import pytest

from config.settings import BotConfig, get_config


class TestBotConfig:
    """Tests for BotConfig class."""

    def test_load_from_env_success(self, sample_env_vars):
        """Test successful loading of configuration from environment."""
        config = BotConfig.load_from_env()

        assert config.discord_token == "test_token_123"
        assert config.database_path == "test_pledge_points.db"
        assert config.points_channel_id == 123456789
        assert isinstance(config.deleted_messages_channel_id, int)

    def test_load_from_env_missing_token(self):
        """Test that missing DISCORD_TOKEN raises ValueError."""
        import os
        from unittest.mock import patch

        env = {"CSV_NAME": "test.db", "CHANNEL_ID": "123"}
        with patch("config.settings.load_dotenv"):  # Don't load .env file
            with patch.dict(os.environ, env, clear=True):
                with pytest.raises(ValueError, match="DISCORD_TOKEN not found"):
                    BotConfig.load_from_env()

    def test_load_from_env_missing_database_path(self):
        """Test that missing CSV_NAME raises ValueError."""
        import os
        from unittest.mock import patch

        env = {"DISCORD_TOKEN": "token", "CHANNEL_ID": "123"}
        with patch("config.settings.load_dotenv"):  # Don't load .env file
            with patch.dict(os.environ, env, clear=True):
                with pytest.raises(ValueError, match="CSV_NAME"):
                    BotConfig.load_from_env()

    def test_load_from_env_missing_channel_id(self):
        """Test that missing CHANNEL_ID raises ValueError."""
        import os
        from unittest.mock import patch

        env = {"DISCORD_TOKEN": "token", "CSV_NAME": "test.db"}
        with patch("config.settings.load_dotenv"):  # Don't load .env file
            with patch.dict(os.environ, env, clear=True):
                with pytest.raises(ValueError, match="CHANNEL_ID not found"):
                    BotConfig.load_from_env()

    def test_load_from_env_invalid_channel_id(self, monkeypatch):
        """Test that non-integer CHANNEL_ID raises ValueError."""
        monkeypatch.setenv("DISCORD_TOKEN", "token")
        monkeypatch.setenv("CSV_NAME", "test.db")
        monkeypatch.setenv("CHANNEL_ID", "not_a_number")

        with pytest.raises(ValueError, match="CHANNEL_ID must be a valid integer"):
            BotConfig.load_from_env()

    def test_config_is_frozen(self, sample_env_vars):
        """Test that BotConfig is immutable (frozen dataclass)."""
        config = BotConfig.load_from_env()

        with pytest.raises(Exception):  # FrozenInstanceError in Python 3.10+
            config.discord_token = "new_token"


class TestGetConfig:
    """Tests for get_config function."""

    def test_get_config_singleton(self, sample_env_vars):
        """Test that get_config returns the same instance."""
        # Reset the global config
        import config.settings

        config.settings.config = None

        config1 = get_config()
        config2 = get_config()

        assert config1 is config2

    def test_get_config_loads_once(self, sample_env_vars, monkeypatch):
        """Test that configuration is loaded only once."""
        # Reset the global config
        import config.settings

        config.settings.config = None

        # Get config multiple times
        config1 = get_config()
        config2 = get_config()

        # Both should have same values
        assert config1.discord_token == config2.discord_token
        assert config1.database_path == config2.database_path
