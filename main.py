# Imports
import asyncio  # Asynchronous I/O support
import os  # File and path operations
import ssl  # Secure connection support
from datetime import datetime  # Date and time handling

import aiohttp  # Add this import at the top with other imports
import discord
import pytz  # type: ignore  # Timezone support
from discord.ext import commands  # Discord bot commands and scheduled tasks
from dotenv import load_dotenv

from PledgePoints.csvutils import create_csv
from commands.admin import setup as setup_admin
from commands.points import setup as setup_points

# Warner: ssl_context until the on_ready function was ai generated because I couldn't be bothered
# Initialize SSL context for secure connections
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Set up Discord bot with required permissions
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
bot = commands.Bot(command_prefix='!', intents=intents)

# Create aiohttp session with SSL context
async def get_session() -> aiohttp.ClientSession:
    return aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context))


# Type ignore for internal discord.py attributes
bot.http._HTTPClient__session = None  # type: ignore
bot.http.get_session = get_session  # type: ignore

# Add start_time attribute to bot
setattr(bot, 'start_time', None)

@bot.event
async def on_ready():
    print(f'Bot is ready! Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')
    
    if bot.start_time is None:  # Only set on first connection
        bot.start_time = datetime.now(pytz.UTC)
        print(f'Start time set to: {bot.start_time}')

    try:
        # Set up command modules
        setup_admin(bot)
        setup_points(bot)
        
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

if __name__ == "__main__":
    asyncio.run(main())

# dfgh
