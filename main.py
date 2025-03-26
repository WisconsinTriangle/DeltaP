# Imports
import asyncio  # Asynchronous I/O support
import os  # File and path operations
import ssl  # Secure connection support
from datetime import datetime  # Date and time handling

import aiohttp  # Add this import at the top with other imports
import pytz  # type: ignore  # Timezone support
from discord.ext import commands  # Discord bot commands and scheduled tasks
from dotenv import load_dotenv

from PledgePoints.approval import get_unapproved_points, change_point_approval, change_approval_with_discrete_values, \
    delete_unapproved_points
from PledgePoints.csvutils import create_csv, read_csv
from PledgePoints.pledges import change_pledge_points
from role.role_checking import *

# Warner: ssl_context until the on_ready function was ai generated because I couldn't be bothered
# Initialize SSL context for secure connections
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Set up Discord bot with required permissions
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
bot = commands.Bot(command_prefix='!', intents=intents)
# Type ignore for dynamic attributes
bot.start_time: Optional[datetime] = None  # type: ignore

# Create aiohttp session with SSL context
async def get_session() -> aiohttp.ClientSession:
    return aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context))

# Type ignore for internal discord.py attributes
bot.http._HTTPClient__session = None  # type: ignore
bot.http.get_session = get_session  # type: ignore

@bot.event
async def on_ready():
    print(f'Bot is ready! Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')
    
    if bot.start_time is None:  # Only set on first connection
        bot.start_time = datetime.now(pytz.UTC)
        print(f'Start time set to: {bot.start_time}')

    try:
        # Synchronize slash commands with Discord's API
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Error synchronizing slash commands: {str(e)}')




load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("DISCORD_TOKEN not found in .env file")

master_point_csv_name = os.getenv('CSV_NAME')
if not master_point_csv_name:
    raise ValueError("CSV_NAME not found in .env file")


# Initialize required CSV files if they don't exist
try:
    if not os.path.exists(master_point_csv_name):
        # Warner: The Default values for columns in the create_csv function are fine here.
        create_csv(master_point_csv_name)

except Exception as e:
    print(f"Error creating CSV files: {str(e)}")
    del e

async def main():
    print('Starting bot...')
    try:
        # First set up the bot
        await bot.login(TOKEN)
        print('Successfully logged in')
        # Then connect and start processing events
        await bot.connect()
        print('Successfully connected to Discord')
    except Exception as e:
        print(f'Error during startup: {str(e)}')
    finally:
        if not bot.is_closed():
            await bot.close()


@bot.tree.command(name="ping", description="Check if the bot is responsive and get its latency")
async def ping(interaction: discord.Interaction):
    # Send initial response and get the timestamp
    start_time = datetime.now(pytz.UTC)
    await interaction.response.send_message("Calculating ping...")

    # Get WebSocket latency
    websocket_latency = round(bot.latency * 1000)  # Convert to milliseconds
    
    # Calculate uptime
    uptime = datetime.now(pytz.UTC) - bot.start_time
    hours = uptime.total_seconds() // 3600
    minutes = (uptime.total_seconds() % 3600) // 60
    seconds = uptime.total_seconds() % 60

    # Create embed for better presentation
    embed = discord.Embed(
        title="🏓 Pong!",
        color=discord.Color.green()
    )

    # Calculate API latency after creating the embed
    api_latency = round((datetime.now(pytz.UTC) - start_time).total_seconds() * 1000)  # Convert to milliseconds

    embed.add_field(name="API Latency", value=f"{api_latency}ms", inline=True)
    embed.add_field(name="WebSocket Latency", value=f"{websocket_latency}ms", inline=True)
    embed.add_field(name="Uptime", value=f"{int(hours)}h {int(minutes)}m {int(seconds)}s", inline=True)

    # Edit the original response with the embed
    await interaction.edit_original_response(content=None, embed=embed)


@bot.tree.command(name="give_take_pledge_points", description="Give or take pledge points from a specific pledge")
async def give_pledge_points(interaction: discord.Interaction, points: int, pledge: str, brother: str, comment: str):
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

    Raises:
        None

    Returns:
        None
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
async def approve(interaction: discord.Interaction, point_id: str) -> bool:
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

    Raises:
        Exception: Raised when there is an issue reading or writing the CSV file, or
            if there's an issue processing the IDs. Corresponding error messages are
            sent to the user.
    Returns:
        bool: Returns True if the points were successfully approved. If the operation
            cannot be completed due to permissions or errors, no value is returned.
    """
    if await check_eboard_role(interaction) is False and await check_info_systems_role(interaction) is False:
        await interaction.response.send_message("You don't have permission to do that.")
        return False
    # Reads in the points csv file
    try:
        df = read_csv(master_point_csv_name)
    except Exception as error:
        await interaction.response.send_message(f"There was an error: {str(error)}")
        return False
    # If theres only one point id to approve
    if "," not in point_id:
        try:
            point_id_int = int(point_id)
            if point_id_int not in get_unapproved_points(df)["ID"].values.tolist():
                await interaction.response.send_message("Error: This ID is not in the unapproved list")
                return False
            df = change_point_approval(df, point_id_int, new_approval=True)
            df.to_csv(master_point_csv_name, index=False)
            await interaction.response.send_message(f"Point {point_id} approved")
            return True
        except Exception as error:
            await interaction.response.send_message(f"There was an error: {str(error)}")
            return False
    # Splits the id string into a list of ints
    ids = [int(ID) for ID in point_id.split(",")]
    try:
        # Changes the points with the given ids
        df = change_approval_with_discrete_values(df, ids, new_approval=True)
        df.to_csv(master_point_csv_name, index=False)
        await interaction.response.send_message(f"Points {point_id} approved")
        return True
    except Exception as error:
        await interaction.response.send_message(f"There was an error: {str(error)}")
        return False


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

    Raises:
        Exception: Any unexpected error encountered during processing is caught
                   and the error message is sent to the user as feedback.
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

if __name__ == "__main__":
    asyncio.run(main())

