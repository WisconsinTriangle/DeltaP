import asyncio
from datetime import datetime, timedelta
from typing import List, Tuple

import discord
import pytz

from PledgePoints.constants import EMOJI_FAILURE, EMOJI_SUCCESS, REACTION_RATE_LIMIT_SECONDS
from PledgePoints.models import PointEntry
from PledgePoints.sqlutils import DatabaseManager
from PledgePoints.validators import parse_point_message


async def fetch_messages_from_days_ago(
    bot: discord.Client, channel_id: int, days_ago: int
) -> list[tuple[discord.User, datetime, str, discord.Message]]:
    """
    Fetch messages from a Discord channel that were sent a certain number of days ago.

    Args:
        bot (discord.Client): The Discord bot instance
        channel_id (int): The ID of the channel to fetch messages from
        days_ago (int): Number of days ago to fetch messages from

    Returns:
        list[tuple[discord.User, datetime, str, discord.Message]]: List of tuples containing (author, created_at, content, message)
    """
    # Get the channel
    channel = bot.get_channel(channel_id)
    if not channel:
        raise ValueError(f"Channel with ID {channel_id} not found")

    # Calculate the target date
    target_date = datetime.now(pytz.UTC) - timedelta(days=days_ago)

    # Fetch messages
    messages = []
    async for message in channel.history(limit=None, after=target_date):
        # Skip messages from bots
        if message.author.bot:
            continue
        messages.append((message.author, message.created_at, message.content, message))

    return messages




async def add_reactions_with_rate_limit(
    messages: List[Tuple[discord.Message, bool]],
    rate_limit: float = REACTION_RATE_LIMIT_SECONDS
):
    """
    Add reactions to messages with rate limiting.

    Adds emoji reactions to Discord messages to indicate validation status.
    Includes rate limiting to avoid hitting Discord API limits.

    Args:
        messages: List of (message, success) tuples where success determines emoji
        rate_limit: Minimum time between reactions in seconds
    """
    for message, success in messages:
        try:
            emoji = EMOJI_SUCCESS if success else EMOJI_FAILURE
            await message.add_reaction(emoji)
            await asyncio.sleep(rate_limit)  # Rate limit the reactions
        except Exception:
            # Skip if we can't add the reaction (permissions, deleted message, etc.)
            continue


async def process_messages(
    messages: list[tuple[discord.User, datetime, str, discord.Message]],
) -> List[PointEntry]:
    """
    Process messages to extract point changes, pledge names, and comments.

    Validates each message against the expected format (+/-N PledgeName Comment)
    and returns a list of PointEntry objects. Also handles adding reactions
    to messages (thumbs up for valid, thumbs down for invalid).

    Args:
        messages: List of tuples containing (author, timestamp, content, message)

    Returns:
        List[PointEntry]: List of validated point entries ready for database insertion
    """
    processed_entries = []
    reaction_queue = []

    for author, timestamp, content, message in messages:
        # Use centralized validator to parse message
        result = parse_point_message(content)

        if result is None:
            # Invalid message - queue failure reaction
            reaction_queue.append((message, False))
            continue

        point_change, pledge, comment = result

        # Create PointEntry object
        entry = PointEntry(
            time=timestamp,
            point_change=point_change,
            pledge=pledge,
            brother=author.display_name,
            comment=comment
        )
        processed_entries.append(entry)
        reaction_queue.append((message, True))

    # Handle reactions separately with rate limiting
    asyncio.create_task(add_reactions_with_rate_limit(reaction_queue))

    return processed_entries


def eliminate_duplicates(
    new_entries: List[PointEntry],
    db_manager: DatabaseManager,
) -> List[PointEntry]:
    """
    Eliminate duplicate point entries by comparing against existing database entries.

    Compares new entries against all existing entries (pending, approved, rejected)
    to avoid duplicate insertions. Uses ISO format for datetime comparison to
    preserve full precision including microseconds and timezone information.

    Args:
        new_entries: List of new point entries to check for duplicates
        db_manager: Database manager instance for querying existing entries

    Returns:
        List[PointEntry]: List of unique entries not already in the database
    """
    # Get all existing points from the database, regardless of approval status
    # We only compare message content (time, points, pledge, brother, comment)
    # and ignore approval-related fields (id, approval_status, approved_by, approval_timestamp)
    old_points = db_manager.get_all_points(status_filter=None)

    # Convert old points to a set of string representations for faster lookup
    old_points_set = set()
    for point in old_points:
        # Convert datetime to ISO format string to preserve full precision
        time_str = point.time.isoformat()
        # Create a tuple of the relevant fields as strings
        point_key = (time_str, str(point.point_change), point.pledge, point.brother, point.comment)
        old_points_set.add(point_key)

    # Filter new entries
    unique_entries = []
    for entry in new_entries:
        # Convert datetime to ISO format string in the same format
        time_str = entry.time.isoformat()
        # Create a tuple of the relevant fields as strings
        entry_key = (time_str, str(entry.point_change), entry.pledge, entry.brother, entry.comment)

        if entry_key not in old_points_set:
            unique_entries.append(entry)

    return unique_entries
