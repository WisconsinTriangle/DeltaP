"""
Constants and business rules for the pledge points system.

This module centralizes all configuration data that may need to be updated,
such as valid pledge names, aliases, and system constants. This makes it
easy to update pledge lists each semester without modifying code logic.

Author: Warner (with AI assistance)
"""

from typing import Dict, List

# =============================================================================
# PLEDGE CONFIGURATION
# =============================================================================

# Valid pledge names for the current semester
# Update this list at the start of each semester
VALID_PLEDGES: List[str] = [
    "Evan",
    "Felix",
    "George",
    "Henrik",
    "Kashyap",
    "Krishiv",
    "Logan",
    "Milo",
    "Nick",
    "Tony",
    "Will",
    "Devin",
]

# Pledge name aliases and nicknames
# Maps common nicknames or alternate spellings to official pledge names
PLEDGE_ALIASES: Dict[str, str] = {
    # Add more aliases as needed
}

# =============================================================================
# DISCORD CONSTANTS
# =============================================================================

# Emoji reactions for message validation
EMOJI_SUCCESS = "👍"  # Valid point submission
EMOJI_FAILURE = "👎"  # Invalid point submission

# Discord message length limits
DISCORD_MESSAGE_MAX_LENGTH = 2000  # Official Discord limit
DISCORD_MESSAGE_SAFE_LENGTH = 1900  # Safe chunking limit with buffer

# Rate limiting for Discord API calls
REACTION_RATE_LIMIT_SECONDS = 0.2  # Minimum time between reactions

# =============================================================================
# VALIDATION CONSTANTS
# =============================================================================

# SQL integer limits for point values
# SQLite INTEGER type range
SQL_INT_MIN = -9223372036854775808
SQL_INT_MAX = 9223372036854775807

# Point entry validation regex
# Matches format: +10, -5, +100, +1.25, -2.5, etc.
POINT_REGEX_PATTERN = r"^([+-]\d+(?:\.\d+)?)"

# =============================================================================
# RANKING DISPLAY
# =============================================================================

# Medal emojis for top 3 pledges in rankings
RANK_MEDALS = {
    1: "🥇",  # Gold
    2: "🥈",  # Silver
    3: "🥉",  # Bronze
}
