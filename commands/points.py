import os
import time
import discord
from discord.ext import commands

from PledgePoints.messages import fetch_messages_from_days_ago, process_messages, eliminate_duplicates
from PledgePoints.pledges import get_pledge_points, rank_pledges, plot_rankings
from PledgePoints.sqlutils import DatabaseManager
from config.settings import get_config
from utils.discord_helpers import (
    send_chunked_message,
    format_point_entry_detailed,
    format_rankings_text,
    format_pending_points_list,
    format_approval_confirmation
)


def setup(bot: commands.Bot):
    """
    Set up all pledge points-related slash commands for the bot.

    Initializes the database manager and registers all command handlers
    with the Discord bot. Commands include updating points, viewing rankings,
    approving/rejecting points, and more.

    Args:
        bot: Discord bot instance to register commands with
    """
    # Load configuration from centralized config
    config = get_config()

    # Initialize the database manager
    db_manager = DatabaseManager(config.database_path)

    @bot.tree.command(name="update_pledge_points", description="Update the point Database.")
    async def update_pledge_points(interaction: discord.Interaction, days_ago: int):
        """
        Fetch and process messages from the points channel to update the database.

        This command scans the configured channel for messages from the specified
        number of days ago, validates them, and adds new point entries to the database.
        Duplicates are automatically filtered out.

        Args:
            interaction: Discord interaction from the slash command
            days_ago: Number of days in the past to fetch messages from
        """
        from role.role_checking import check_brother_role
        if not await check_brother_role(interaction):
            await interaction.response.send_message("You don't have permission to do that. Brother role required.",
                                                    ephemeral=True)
            return
        try:
            await interaction.response.send_message(f"Updating pledge points for {days_ago} days ago")
            start_time_1 = time.time()
            # Fetch messages from Discord using config
            messages = await fetch_messages_from_days_ago(bot, config.points_channel_id, days_ago)

            if not messages:
                await interaction.followup.send("No messages found for the specified time period.")
                return
            end_time_1 = time.time()
            # Process messages into PointEntry objects
            start_time_2 = time.time()
            new_entries = await process_messages(messages)
            end_time_2 = time.time()

            start_time_3 = time.time()
            # Eliminate duplicates using the database manager
            unique_entries = eliminate_duplicates(new_entries, db_manager)

            if not unique_entries:
                await interaction.followup.send("No new points to add to the database.")
                return
            end_time_3 = time.time()
            # Add new entries to the database

            count = db_manager.add_point_entries(unique_entries)
            await interaction.followup.send(f"Successfully added {count} new points to the database. \n"
                                            f"Fetching Messages took {(end_time_1 - start_time_1):.2f} seconds.\n"
                                            f"Processing Messages took {(end_time_2 - start_time_2):.2f} seconds.\n"
                                            f"Eliminating Duplicates took {(end_time_3 - start_time_3):.2f} seconds.\n")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")
            raise


    @bot.tree.command(name="pledge_rankings", description="Show rankings of all pledges by total points.")
    async def pledge_rankings(interaction: discord.Interaction):
        """
        Display a leaderboard of all pledges ranked by total approved points.

        Shows pledges in descending order with medal emojis for the top 3.
        Only includes approved points in the calculations.

        Args:
            interaction: Discord interaction from the slash command
        """
        from role.role_checking import check_brother_role
        if not await check_brother_role(interaction):
            await interaction.response.send_message("You don't have permission to do that. Brother role required.", ephemeral=True)
            return
        try:
            await interaction.response.send_message("Fetching pledge rankings...")

            # Get pledge points and rankings using database manager
            points = get_pledge_points(db_manager)
            rankings_df = rank_pledges(points)
            rankings = [(pledge, int(total_points)) for pledge, total_points in rankings_df.items()]

            if not rankings:
                await interaction.followup.send("No pledge data found in the database.")
                return

            # Format the rankings using utility function
            ranking_text = format_rankings_text(rankings)

            # Send with automatic chunking if needed
            await send_chunked_message(interaction, ranking_text)
        except Exception as e:
            await interaction.followup.send(f"An error occurred while fetching rankings: {str(e)}")
            raise

    @bot.tree.command(name="plot_rankings", description="Plot rankings of all pledges by total points.")
    async def plot_rankings_command(interaction: discord.Interaction):
        """
        Generate and display a bar chart of pledge rankings.

        Creates a visual representation of pledge points showing all pledges
        ranked by their total approved points.

        Args:
            interaction: Discord interaction from the slash command
        """
        from role.role_checking import check_brother_role
        if not await check_brother_role(interaction):
            await interaction.response.send_message("You don't have permission to do that. Brother role required.", ephemeral=True)
            return
        try:
            await interaction.response.send_message("Generating pledge rankings plot...")

            # Get pledge points and rankings using database manager
            points = get_pledge_points(db_manager)
            rankings_df = rank_pledges(points)

            if rankings_df.empty:
                await interaction.followup.send("No pledge data found in the database.")
                return

            # Generate plot and send as file
            plot_file = plot_rankings(rankings_df)
            await interaction.followup.send(file=discord.File(plot_file))

            # Clean up the generated plot file
            if os.path.exists(plot_file):
                os.remove(plot_file)

        except Exception as e:
            await interaction.followup.send(f"An error occurred while generating the plot: {str(e)}")
            raise

    @bot.tree.command(name="view_pending_points", description="View all pending point submissions that need approval")
    async def view_pending_points(interaction: discord.Interaction):
        """
        Display all point submissions awaiting approval.

        Shows detailed information for each pending entry including timestamp,
        brother who submitted, points, pledge, and comment.

        Args:
            interaction: Discord interaction from the slash command
        """
        from role.role_checking import check_brother_role
        if not await check_brother_role(interaction):
            await interaction.response.send_message("You don't have permission to do that. Brother role required.", ephemeral=True)
            return
        try:
            await interaction.response.send_message("Fetching pending points...")

            # Get pending points using database manager
            pending_entries = db_manager.get_pending_points()

            if not pending_entries:
                await interaction.followup.send("No pending points found.")
                return

            # Format the pending points using utility function
            pending_text = format_pending_points_list(pending_entries)

            # Send with automatic chunking if needed
            await send_chunked_message(interaction, pending_text)

        except Exception as e:
            await interaction.followup.send(f"An error occurred while fetching pending points: {str(e)}")
            raise

    @bot.tree.command(name="approve_points", description="Approve specific point submissions by ID or all pending points")
    async def approve_points(interaction: discord.Interaction, point_ids: str):
        """
        Approve pending point submissions.

        Allows E-Board members to approve point submissions by ID or approve all
        pending points at once using 'all'. Approved points count toward pledge rankings.

        Args:
            interaction: Discord interaction from the slash command
            point_ids: Comma-separated list of IDs (e.g., "1,2,3") or "all" for all pending
        """
        try:
            # Check if user has Executive Board role
            from role.role_checking import check_eboard_role, check_info_systems_role
            if not (await check_eboard_role(interaction) or await check_info_systems_role(interaction)):
                await interaction.response.send_message("You don't have permission to approve points. Executive Board role required.", ephemeral=True)
                return

            await interaction.response.send_message("Processing approval...")

            approve_all = point_ids.strip().lower() == "all"
            approver = interaction.user.display_name

            if approve_all:
                # Approve all pending points using database manager
                approved_entries = db_manager.approve_all_pending(approver)

                if not approved_entries:
                    await interaction.followup.send("No pending points found to approve.")
                    return

                # Format response using utility function
                approved_text = format_approval_confirmation(approved_entries, approved=True)
                approved_text = approved_text.replace("Approved", f"Approved ALL ({len(approved_entries)})")

                # Send with automatic chunking if needed
                await send_chunked_message(interaction, approved_text)
            else:
                # Parse point IDs
                try:
                    ids = [int(id.strip()) for id in point_ids.split(',')]
                except ValueError:
                    await interaction.followup.send("Invalid point IDs. Please provide comma-separated numbers or 'all'.")
                    return

                # Approve specific points using database manager
                approved_entries = db_manager.approve_points(ids, approver)

                if not approved_entries:
                    await interaction.followup.send("No pending points found with the provided IDs.")
                    return

                # Format response using utility function
                approved_text = format_approval_confirmation(approved_entries, approved=True)

                # Send with automatic chunking if needed
                await send_chunked_message(interaction, approved_text)

        except Exception as e:
            # If the error is due to message length, send a more helpful message
            error_message = str(e)
            if "Must be 2000 or fewer in length" in error_message or "Invalid Form Body" in error_message:
                await interaction.followup.send("The approval message was too long to send. Please approve fewer points at a time or contact an admin.")
            else:
                await interaction.followup.send(f"An error occurred while approving points: {error_message}")
            raise

    @bot.tree.command(name="reject_points", description="Reject specific point submissions by ID")
    async def reject_points(interaction: discord.Interaction, point_ids: str):
        """
        Reject pending point submissions.

        Allows E-Board members to reject point submissions by ID. Rejected points
        will not count toward pledge rankings.

        Args:
            interaction: Discord interaction from the slash command
            point_ids: Comma-separated list of IDs to reject (e.g., "1,2,3")
        """
        try:
            # Check if user has Executive Board role
            from role.role_checking import check_eboard_role, check_info_systems_role
            if not (await check_eboard_role(interaction) or await check_info_systems_role(interaction)):
                await interaction.response.send_message("You don't have permission to reject points. Executive Board role required.", ephemeral=True)
                return

            await interaction.response.send_message("Processing rejection...")

            # Parse point IDs
            try:
                ids = [int(id.strip()) for id in point_ids.split(',')]
            except ValueError:
                await interaction.followup.send("Invalid point IDs. Please provide comma-separated numbers.")
                return

            # Reject points using database manager
            rejector = interaction.user.display_name
            rejected_entries = db_manager.reject_points(ids, rejector)

            if not rejected_entries:
                await interaction.followup.send("No pending points found with the provided IDs.")
                return

            # Format response using utility function
            rejected_text = format_approval_confirmation(rejected_entries, approved=False)

            await interaction.followup.send(rejected_text)

        except Exception as e:
            await interaction.followup.send(f"An error occurred while rejecting points: {str(e)}")
            raise

    @bot.tree.command(name="view_point_details", description="View detailed information about a specific point entry")
    async def view_point_details(interaction: discord.Interaction, point_id: int):
        """
        Display detailed information about a specific point entry.

        Shows all information including timestamp, brother, points, pledge,
        comment, and approval status with approver and timestamp.

        Args:
            interaction: Discord interaction from the slash command
            point_id: Database ID of the point entry to view
        """
        from role.role_checking import check_brother_role
        if not await check_brother_role(interaction):
            await interaction.response.send_message("You don't have permission to do that. Brother role required.", ephemeral=True)
            return
        try:
            await interaction.response.send_message("Fetching point details...")

            # Get point entry using database manager
            entry = db_manager.get_point_by_id(point_id)

            if not entry:
                await interaction.followup.send(f"No point entry found with ID {point_id}.")
                return

            # Format detailed entry using utility function
            details_text = f"📊 **Point Entry Details - ID {entry.entry_id}**\n\n"
            details_text += format_point_entry_detailed(entry)

            await interaction.followup.send(details_text)

        except Exception as e:
            await interaction.followup.send(f"An error occurred while fetching point details: {str(e)}")
            raise
