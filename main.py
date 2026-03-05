# Imports
import asyncio  # Asynchronous I/O support
import ssl  # Secure connection support
from datetime import datetime, timedelta  # Date and time handling

import aiohttp  # Add this import at the top with other imports
import discord
import pytz  # type: ignore  # Timezone support
from discord.ext import commands  # Discord bot commands and scheduled tasks

from commands.admin import setup as setup_admin
from commands.points import setup as setup_points
from config.settings import get_config

# Warner: ssl_context until the on_ready function was AI generated because I couldn't be bothered
# Initialize SSL context for secure connections
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Set up Discord bot with required permissions
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
intents.guilds = True  # Enable guild events
intents.messages = True  # Enable message events (including deletions)
bot = commands.Bot(command_prefix="!", intents=intents)


# Create aiohttp session with SSL context
async def get_session() -> aiohttp.ClientSession:
    return aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context))


# Type ignore for internal discord.py attributes
bot.http._HTTPClient__session = None  # type: ignore
bot.http.get_session = get_session  # type: ignore

# Add start_time attribute to bot
setattr(bot, "start_time", None)

AUTISMBOARD_CHANNEL_ID = 1447396336428384256


async def export_channel_to_markdown(channel: discord.TextChannel, months: int = 2) -> None:
    """Fetch messages from the past `months` months and save to a markdown file."""
    after_date = datetime.now(pytz.UTC) - timedelta(days=months * 30)
    messages = []

    print(f"Fetching messages from #{channel.name} since {after_date.date()}...")
    async for message in channel.history(limit=None, after=after_date, oldest_first=True):
        messages.append(message)

    print(f"Fetched {len(messages)} messages from #{channel.name}")

    filename = f"{channel.name}_export.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# #{channel.name} — Message Export\n\n")
        f.write(f"Exported: {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M UTC')}\n")
        f.write(f"Period: {after_date.strftime('%Y-%m-%d')} to {datetime.now(pytz.UTC).strftime('%Y-%m-%d')}\n")
        f.write(f"Total messages: {len(messages)}\n\n---\n\n")

        current_date = None
        for msg in messages:
            msg_date = msg.created_at.strftime("%Y-%m-%d")
            if msg_date != current_date:
                current_date = msg_date
                f.write(f"## {msg_date}\n\n")

            timestamp = msg.created_at.strftime("%H:%M")
            author = msg.author.display_name
            content = msg.content if msg.content else ""

            f.write(f"**{author}** ({timestamp})\n")
            if content:
                f.write(f"{content}\n")
            if msg.attachments:
                for att in msg.attachments:
                    f.write(f"[Attachment: {att.filename}]({att.url})\n")
            if msg.embeds:
                f.write(f"*[{len(msg.embeds)} embed(s)]*\n")
            f.write("\n")

    print(f"Saved {len(messages)} messages to {filename}")


@bot.event
async def on_ready():
    global conn
    print(f"Bot is ready! Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("------")
    if bot.start_time is None:  # Only set on first connection
        bot.start_time = datetime.now(pytz.UTC)
        print(f"Start time set to: {bot.start_time}")

    # Print all channel IDs
    for guild in bot.guilds:
        print(f"Guild: {guild.name} (ID: {guild.id})")
        for channel in guild.channels:
            print(f"  #{channel.name} (ID: {channel.id}, Type: {channel.type})")

    # Export autismboard messages to markdown
    autismboard = bot.get_channel(AUTISMBOARD_CHANNEL_ID)
    if autismboard:
        await export_channel_to_markdown(autismboard)
    else:
        print(f"Could not find autismboard channel (ID: {AUTISMBOARD_CHANNEL_ID})")

    try:
        # Set up command modules
        setup_admin(bot)
        setup_points(bot)

        # Synchronize slash commands with Discord's API
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")

        # Test the deleted messages channel access
        config = get_config()
        test_channel = bot.get_channel(config.deleted_messages_channel_id)
        if test_channel:
            print(
                f"✅ Successfully found target channel: {test_channel.name} in {test_channel.guild.name}"
            )
        else:
            print(
                f"❌ Could not find target channel with ID {config.deleted_messages_channel_id}"
            )
            print("Available channels:")
            for guild in bot.guilds:
                print(f"  Guild: {guild.name} (ID: {guild.id})")
                for channel in guild.text_channels:
                    print(f"    - {channel.name} (ID: {channel.id})")
    except Exception as e:
        print(f"Error synchronizing slash commands: {str(e)}")


@bot.event
async def on_message_delete(message):
    """
    Event handler that triggers when a message is deleted.
    Sends the deleted message content to a specific channel for logging.
    """
    print(
        f"Message deletion detected! Message ID: {message.id}, Author: {message.author}"
    )

    try:
        # Get configuration
        config = get_config()

        # Get the target channel from config
        channel = bot.get_channel(config.deleted_messages_channel_id)
        if not channel:
            print(
                f"Warning: Could not find channel with ID {config.deleted_messages_channel_id}"
            )
            return

        print(f"Target channel found: {channel.name} ({channel.id})")

        # Skip if the message was from a bot
        if message.author.bot:
            print("Skipping bot message deletion")
            return

        # Create embed for the deleted message
        embed = discord.Embed(
            title="🗑️ Message Deleted",
            color=discord.Color.red(),
            timestamp=datetime.now(pytz.UTC),
        )

        # Add message details
        embed.add_field(
            name="Author",
            value=f"{message.author.mention} ({message.author.name}#{message.author.discriminator})",
            inline=True,
        )
        embed.add_field(
            name="Channel",
            value=f"{message.channel.mention} ({message.channel.name})",
            inline=True,
        )
        embed.add_field(name="Message ID", value=message.id, inline=True)

        # Add message content (truncate if too long)
        content = message.content if message.content else "*No text content*"
        if len(content) > 1024:
            content = content[:1021] + "..."

        embed.add_field(name="Content", value=content, inline=False)

        # Add attachments info if any
        if message.attachments:
            attachment_names = [att.filename for att in message.attachments]
            embed.add_field(
                name="Attachments", value=", ".join(attachment_names), inline=False
            )

        # Add embeds info if any
        if message.embeds:
            embed.add_field(
                name="Embeds",
                value=f"{len(message.embeds)} embed(s) were present",
                inline=False,
            )

        # Send the embed to the target channel
        await channel.send(embed=embed)
        print(f"Successfully logged deleted message to {channel.name}")

    except Exception as e:
        print(f"Error handling message deletion: {str(e)}")


# Load configuration from centralized config module
config = get_config()
TOKEN = config.discord_token


async def main():
    print("Starting bot...")
    try:
        # First set up the bot
        await bot.login(TOKEN)
        print("Successfully logged in")
        # Then connect and start processing events
        await bot.connect()
        print("Successfully connected to Discord")
    except Exception as e:
        print(f"Error during startup: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
