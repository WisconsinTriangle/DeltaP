import time
from datetime import datetime
import discord
import pytz
from discord.ext import commands

from role.role_checking import check_info_systems_role


def setup(bot: commands.Bot):
    @bot.tree.command(
        name="ping", description="Check if the bot is responsive and get its latency"
    )
    async def ping(interaction: discord.Interaction):
        # Send initial response and get the timestamp
        await interaction.response.send_message("Calculating ping...")

        # Get WebSocket latency. This is a single request and the response.
        websocket_latency = round(bot.latency * 1000)  # Convert to milliseconds

        # Calculate uptime

        # Create embed for better presentation
        embed: discord.Embed = discord.Embed(
            title="🏓 Pong!", color=discord.Color.green()
        )

        embed.add_field(
            name="WebSocket Latency", value=f"{websocket_latency}ms", inline=True
        )
        # Edit the original response with the embed
        await interaction.edit_original_response(content=None, embed=embed)

    @bot.tree.command(name="shutdown", description="Shut the bot down remotely")
    async def shutdown(interaction: discord.Interaction):
        """
        Sets up the bot with a remote shutdown command. Shuts down the bot securely
        when the appropriate user permission is detected. The command ensures only
        authorized roles can invoke shutdown.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction context for the shutdown command, typically initiated by
            a user command.

        Raises
        ------
        None

        Returns
        -------
        None
        """
        if await check_info_systems_role(interaction) is False:
            await interaction.response.send_message(
                "You don't have permission to do that."
            )
            return
        await interaction.response.send_message("Shutting down...")
        time.sleep(1)
        await bot.close()
