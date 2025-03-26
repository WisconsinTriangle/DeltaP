import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from PledgePoints.approval import get_unapproved_points, change_point_approval, change_approval_with_discrete_values, \
    delete_unapproved_points
from PledgePoints.csvutils import read_csv
from PledgePoints.pledges import change_pledge_points
from role.role_checking import check_brother_role, check_eboard_role, check_info_systems_role

load_dotenv()
master_point_csv_name = os.getenv('CSV_NAME')
if not master_point_csv_name:
    raise ValueError("CSV_NAME not found in .env file")


def setup(bot: commands.Bot):
    @bot.tree.command(name="give_take_pledge_points", description="Give or take pledge points from a specific pledge")
    async def give_pledge_points(interaction: discord.Interaction, points: int, pledge: str, brother: str,
                                 comment: str):
        """
        Handles the command to give or deduct pledge points for a specific pledge. If the user is
        not authorized, the operation fails. The function ensures valid range for points and updates
        the pledge data accordingly in the master CSV file. Errors are logged, and users are notified
        if operations fail.

        Parameters:
            interaction (discord.Interaction): The interaction object representing the command invocation.
            points (int): The amount of pledge points to add or subtract. Must be in range -128 to 127.
            pledge (str): Name of the pledge to modify.
            brother (str): Name of the person responsible for the action.
            comment (str): A comment or note explaining the modification.
        """
        if await check_brother_role(interaction) is False:
            await interaction.response.send_message("Naughty Pledge trying to edit points.")
            return
        points = int(points)
        if not points in range(-128, 128):
            await interaction.response.send_message("Points must be an integer within the range -128,127.")
            return
        pledge = pledge.title()
        try:
            df = read_csv(master_point_csv_name)
            df = change_pledge_points(df, pledge=pledge, brother=brother, comment=comment, points=points)
            df.to_csv(master_point_csv_name, index=False)
            if points >= 0:
                points_str = f"+{points}"
            else:
                points_str = str(points)
            await interaction.response.send_message(f"{brother}: {points_str} {pledge} {comment}")
        except Exception as error:
            print(error)
            await interaction.response.send_message(f"There was an error: {str(error)}")

    @bot.tree.command(name="list_pending_points", description="List all points that have yet to be approved")
    async def list_pending_points(interaction: discord.Interaction):
        """
        Command to list all unapproved points. It retrieves and formats a list of points that
        have not yet been approved by reading a CSV file and generating a response message
        to display the results. If the command is attempted by a user without appropriate
        permissions, an error message is sent.

        Arguments:
            interaction (discord.Interaction): The interaction object representing the
                command invocation context.
        """
        if await check_brother_role(interaction) is False:
            await interaction.response.send_message("Naughty Pledge trying to use the points bot")
            return
        df = read_csv(master_point_csv_name)
        unapproved_points_df = get_unapproved_points(df)
        if len(unapproved_points_df) == 0:
            await interaction.response.send_message("No pending points to list.")
        unapproved_points_list = unapproved_points_df.values.tolist()
        response = ""
        for points in unapproved_points_list:
            if points[2] >= 0:
                points_str = f"+{points[2]}"
            else:
                points_str = str(points[2])
            entry = f"ID: {points[0]}. {points_str} {points[3]} {points[5]} - {points[4]}\n"
            response = response + entry
        await interaction.response.send_message(response)

    @bot.tree.command(name="approve",
                      description="Approve points. Enter points like 4,3,6)")
    async def approve(interaction: discord.Interaction, point_id: str):
        """
        Approves specific points by their IDs. The points can either be a single ID or a
        comma-separated list of IDs. The command validates the user's role permissions
        before proceeding. Points' approval status is updated in the points CSV file, and
        a confirmation message is sent upon successful execution.

        Args:
            interaction (discord.Interaction): The interaction object containing data
                about the command and user invoking it.
            point_id (str): A string containing a single point ID or a list of point IDs
                in a comma-separated format to be approved.
        """
        if await check_eboard_role(interaction) is False and await check_info_systems_role(interaction) is False:
            await interaction.response.send_message("You don't have permission to do that.")
            return
        # Reads in the points csv file
        try:
            df = read_csv(master_point_csv_name)
        except Exception as error:
            await interaction.response.send_message(f"There was an error: {str(error)}")
            return
        # If theres only one point id to approve
        if "," not in point_id:
            try:
                point_id = int(point_id)
                if point_id not in get_unapproved_points(df)["ID"].values.tolist():
                    await interaction.response.send_message("Error: This ID is not in the unapproved list")
                    return
                df = change_point_approval(df, point_id, new_approval=True)
                df.to_csv(master_point_csv_name, index=False)
                await interaction.response.send_message(f"Point {point_id} approved")
                return True
            except Exception as error:
                await interaction.response.send_message(f"There was an error: {str(error)}")
        # Splits the id string into a list of ints
        ids = point_id.split(",")
        for idx, ID in enumerate(ids):
            ids[idx] = int(ID)
        try:
            # Changes the points with the given ids
            df = change_approval_with_discrete_values(df, ids, new_approval=True)
            df.to_csv(master_point_csv_name, index=False)
            await interaction.response.send_message(f"Points {point_id} approved")
            return True
        except Exception as error:
            await interaction.response.send_message(f"There was an error: {str(error)}")

    @bot.tree.command(name="delete_unapproved_points", description="Delete all points that have not been approved.")
    async def delete_unapproved(interaction: discord.Interaction):
        """
        Deletes all unapproved points from a dataset. The command is only executable
        by users with specific roles defined in the system. If no unapproved points
        are identified, the caller is notified. Any exceptions raised during execution
        are also reported back to the caller.

        Args:
            interaction (discord.Interaction): The interaction object representing the
                                                user's command invocation.
        """
        if await check_eboard_role(interaction) is False and await check_info_systems_role(interaction) is False:
            await interaction.response.send_message("I'm sorry Dave I can't do that. Notifying Standards board")
            return

        try:
            df = read_csv(master_point_csv_name)
            original_length = len(df)
            df2 = delete_unapproved_points(df)

            if len(df2) == original_length:
                await interaction.response.send_message("No unapproved points to delete.")
                return

            df2.to_csv(master_point_csv_name, index=False)
            await interaction.response.send_message("Successfully deleted all unapproved points")

        except Exception as error:
            await interaction.response.send_message(f"An error occurred: {str(error)}")
