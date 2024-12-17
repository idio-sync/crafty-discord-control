import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot setup
bot = discord.Bot(
    intents=discord.Intents.all(),
    debug_guilds=[int(os.getenv('DISCORD_GUILD_ID'))]  # Optional: for faster command registration during development
)

@bot.event
async def on_ready():
    print(f'Bot is ready as {bot.user}')

# Load the cog
bot.load_extension('server_manager')

# Run the bot
bot.run(os.getenv('DISCORD_TOKEN'))
