"""
Discord-specific utility functions for message formatting and handling.

This module provides reusable utility functions for common Discord operations
such as chunking long messages, formatting responses, and handling embeds.

Author: Warner (with AI assistance)
"""

from datetime import datetime
from typing import List

import discord

from PledgePoints.constants import DISCORD_MESSAGE_SAFE_LENGTH, RANK_MEDALS
from PledgePoints.models import PointEntry


async def send_chunked_message(
    interaction: discord.Interaction,
    text: str,
    chunk_size: int = DISCORD_MESSAGE_SAFE_LENGTH,
) -> None:
    """
    Send a long message by splitting it into chunks if necessary.

    Discord has a 2000 character limit for messages. This function automatically
    splits long messages into multiple followup messages if needed.

    Args:
        interaction: Discord interaction to send messages through
        text: The full text to send (may exceed Discord's limit)
        chunk_size: Maximum size of each chunk (default: 1900 for safety buffer)
    """
    if len(text) <= chunk_size:
        await interaction.followup.send(text)
    else:
        # Split into chunks
        chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
        for chunk in chunks:
            await interaction.followup.send(chunk)


def format_approval_status(entry: PointEntry) -> str:
    """
    Format the approval status of a point entry for display.

    Creates a human-readable status string with appropriate emoji and details
    about who approved/rejected and when.

    Args:
        entry: Point entry with approval information

    Returns:
        str: Formatted approval status string with emoji
    """
    if entry.approval_status == "approved":
        status = f"✅ **Approved** by {entry.approved_by}"
        if entry.approval_timestamp:
            status += f" on {entry.approval_timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        return status
    elif entry.approval_status == "rejected":
        status = f"❌ **Rejected** by {entry.approved_by}"
        if entry.approval_timestamp:
            status += f" on {entry.approval_timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        return status
    else:
        return "⏳ **Pending Approval**"


def format_point_entry_summary(entry: PointEntry) -> str:
    """
    Format a point entry as a single-line summary.

    Args:
        entry: Point entry to format

    Returns:
        str: Formatted summary line
    """
    return f"**ID {entry.entry_id}**: {entry.brother} → {entry.pledge} ({entry.point_change:+d} points)"


def format_point_entry_detailed(entry: PointEntry) -> str:
    """
    Format a point entry with full details for display.

    Creates a multi-line formatted display of all point entry information
    including time, brother, points, pledge, comment, and approval status.

    Args:
        entry: Point entry to format

    Returns:
        str: Multi-line formatted string with all entry details
    """
    time_formatted = entry.time.strftime("%Y-%m-%d %H:%M:%S")
    approval_info = format_approval_status(entry)

    details = f"**ID: {entry.entry_id}**\n"
    details += f"⏰ Time: {time_formatted}\n"
    details += f"👤 Brother: {entry.brother}\n"
    details += f"📊 Points: {entry.point_change:+d}\n"
    details += f"🎯 Pledge: {entry.pledge}\n"
    details += f"💬 Comment: {entry.comment}\n"
    details += f"🔍 Status: {approval_info}\n"

    return details


def format_rankings_text(rankings: List[tuple[str, int]]) -> str:
    """
    Format pledge rankings as text with medal emojis for top 3.

    Args:
        rankings: List of (pledge_name, total_points) tuples sorted by points descending

    Returns:
        str: Formatted rankings text with medals and point totals
    """
    if not rankings:
        return "No rankings data available."

    text = "🏆 **Pledge Rankings by Total Points**\n\n"

    for i, (pledge, total_points) in enumerate(rankings, 1):
        # Add medal emoji for top 3, otherwise use number
        medal = RANK_MEDALS.get(i, f"{i}.")
        text += f"{medal} **{pledge}**: {total_points:,} points\n"

    return text


def format_pending_points_list(entries: List[PointEntry]) -> str:
    """
    Format a list of pending point entries for display.

    Args:
        entries: List of pending point entries

    Returns:
        str: Formatted list of pending points with details
    """
    if not entries:
        return "No pending points found."

    text = "📋 **Pending Point Submissions**\n\n"

    for entry in entries:
        text += format_point_entry_detailed(entry) + "\n"

    return text


def format_approval_confirmation(
    entries: List[PointEntry], approved: bool = True
) -> str:
    """
    Format a confirmation message for approved or rejected points.

    Args:
        entries: List of point entries that were approved/rejected
        approved: True for approval message, False for rejection

    Returns:
        str: Formatted confirmation message
    """
    if not entries:
        return "No entries to confirm."

    action = "Approved" if approved else "Rejected"
    emoji = "✅" if approved else "❌"

    text = f"{emoji} **{action} {len(entries)} point submission(s):**\n\n"

    for entry in entries:
        text += format_point_entry_summary(entry) + "\n"

    return text
