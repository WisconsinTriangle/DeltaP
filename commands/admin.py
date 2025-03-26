from datetime import datetime

import discord
import pytz
from discord.ext import commands


def setup(bot: commands.Bot):
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
