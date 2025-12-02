"""
Centralized configuration management for the DeltaP Discord bot.

This module loads and validates all environment variables and configuration
settings at startup, providing a single source of truth for all config values.

Author: Warner (with AI assistance)
"""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass(frozen=True)
class BotConfig:
    """
    Main configuration for the Discord bot.

    All configuration values are loaded from environment variables and validated
    at startup. This class uses frozen dataclass to ensure immutability.

    Attributes:
        discord_token (str): Discord bot authentication token
        database_path (str): Path to the SQLite database file
        points_channel_id (int): Discord channel ID for point submissions
        deleted_messages_channel_id (int): Discord channel ID for deleted message logs
    """

    discord_token: str
    database_path: str
    points_channel_id: int
    deleted_messages_channel_id: int

    @classmethod
    def load_from_env(cls) -> "BotConfig":
        """
        Load configuration from environment variables.

        Reads .env file and validates all required configuration values.
        Raises ValueError if any required values are missing or invalid.

        Returns:
            BotConfig: Validated configuration object

        Raises:
            ValueError: If required environment variables are missing or invalid
        """
        # Load environment variables from .env file
        load_dotenv()

        # Discord token
        discord_token = os.getenv("DISCORD_TOKEN")
        if not discord_token:
            raise ValueError("DISCORD_TOKEN not found in .env file")

        # Database path (formerly CSV_NAME - misleading name kept for compatibility)
        database_path = os.getenv("CSV_NAME")
        if not database_path:
            raise ValueError("CSV_NAME (database path) not found in .env file")

        # Points channel ID
        channel_id_str = os.getenv("CHANNEL_ID")
        if not channel_id_str:
            raise ValueError("CHANNEL_ID not found in .env file")

        try:
            points_channel_id = int(channel_id_str)
        except ValueError:
            raise ValueError(
                f"CHANNEL_ID must be a valid integer, got {channel_id_str}"
            )

        # Deleted messages channel ID (hardcoded value moved to config)
        # This channel ID was previously hardcoded in main.py
        deleted_messages_channel_id = 1160689874299523133

        return cls(
            discord_token=discord_token,
            database_path=database_path,
            points_channel_id=points_channel_id,
            deleted_messages_channel_id=deleted_messages_channel_id,
        )


# Global configuration instance
# This is loaded once at module import and reused throughout the application
config: Optional[BotConfig] = None


def get_config() -> BotConfig:
    """
    Get the global configuration instance.

    Loads configuration on first call and returns cached instance thereafter.
    This ensures config is loaded only once and shared across the application.

    Returns:
        BotConfig: The global configuration object

    Raises:
        ValueError: If configuration cannot be loaded
    """
    global config
    if config is None:
        config = BotConfig.load_from_env()
    return config
