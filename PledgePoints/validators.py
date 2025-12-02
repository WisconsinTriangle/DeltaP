"""
Validation functions for pledge points data.

This module provides validation and normalization functions for point entries,
separating validation logic from parsing and processing logic.

Author: Warner (with AI assistance)
"""

import re
from typing import Optional, Tuple

from PledgePoints.constants import (
    PLEDGE_ALIASES,
    POINT_REGEX_PATTERN,
    SQL_INT_MAX,
    SQL_INT_MIN,
    VALID_PLEDGES,
)


def validate_point_change(value: int) -> bool:
    """
    Validate that a point change value is within acceptable limits.

    Checks that the point value fits within SQLite INTEGER type range.

    Args:
        value: Point change value to validate

    Returns:
        bool: True if valid, False otherwise
    """
    return SQL_INT_MIN <= value <= SQL_INT_MAX


def normalize_pledge_name(name: str) -> str:
    """
    Normalize a pledge name using title case and alias mapping.

    Converts the name to title case and applies any configured aliases
    (e.g., "Matt" → "Matthew", "Ozempic" → "Eli").

    Args:
        name: Raw pledge name from message

    Returns:
        str: Normalized pledge name
    """
    # Convert to title case
    normalized = name.title()

    # Apply alias mapping if exists
    if normalized in PLEDGE_ALIASES:
        normalized = PLEDGE_ALIASES[normalized]

    return normalized


def validate_pledge_name(name: str) -> Optional[str]:
    """
    Validate and normalize a pledge name.

    Checks if the name (after normalization) is in the list of valid pledges.
    Returns the normalized name if valid, None otherwise.

    Args:
        name: Pledge name to validate

    Returns:
        Optional[str]: Normalized pledge name if valid, None if invalid
    """
    normalized = normalize_pledge_name(name)

    if normalized in VALID_PLEDGES:
        return normalized

    return None


def parse_point_message(content: str) -> Optional[Tuple[int, str, str]]:
    """
    Parse a point submission message into its components.

    Expected format: "+10 PledgeName Some comment about the points"
    or: "-5 Matt Being late to chapter"

    Args:
        content: Message content to parse

    Returns:
        Optional[Tuple[int, str, str]]: (point_change, pledge_name, comment)
                                         or None if invalid format

    Examples:
        >>> parse_point_message("+10 Eli Great job at recruitment")
        (10, "Eli", "Great job at recruitment")

        >>> parse_point_message("-5 Matt Being late")
        (-5, "Matthew", "Being late")  # Matt is aliased to Matthew

        >>> parse_point_message("invalid message")
        None
    """
    # Check for empty content
    if not content.strip():
        return None

    # Extract point change using regex
    point_match = re.match(POINT_REGEX_PATTERN, content)
    if not point_match:
        return None

    # Parse point value (accept floats and round to nearest int)
    try:
        point_change = round(float(point_match.group(1)))
    except ValueError:
        return None

    # Validate point value
    if not validate_point_change(point_change):
        return None

    # Extract remaining content after the point value
    remaining_content = content[len(point_match.group(1)) :].strip()

    # Split into pledge name and comment
    parts = remaining_content.split(" ", 1)
    if len(parts) < 2:
        return None

    raw_pledge = parts[0]
    raw_comment = parts[1].strip()

    # Handle "to" prefix (e.g., "+10 to Eli for great work")
    if raw_pledge.lower() == "to":
        # Extract actual pledge name from comment
        comment_parts = raw_comment.split(" ", 1)
        if len(comment_parts) < 2:
            return None
        raw_pledge = comment_parts[0]
        raw_comment = comment_parts[1].strip()

    # Validate and normalize pledge name
    pledge = validate_pledge_name(raw_pledge)
    if pledge is None:
        return None

    return point_change, pledge, raw_comment
