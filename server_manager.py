import discord
from discord.ext import commands, tasks
import aiohttp
import ssl
import json
import os
from dotenv import load_dotenv
import logging
from enum import Enum
from datetime import datetime, timedelta
from functools import wraps

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('minecraft_bot')

# Load environment variables
load_dotenv()

class ServerActions(Enum):
    START_SERVER = "start_server"
    STOP_SERVER = "stop_server"
    RESTART_SERVER = "restart_server"
    BACKUP_SERVER = "backup_server"

# Server configuration mapping
SERVERS = {
    server_name: server_id
    for server_name, server_id in [
        item.split(':') for item in os.getenv('MINECRAFT_SERVERS', '').split(',')
        if ':' in item
    ]
}

# Get configuration from environment variables
ALLOWED_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', 0))
AUTO_SHUTDOWN_MINUTES = int(os.getenv('AUTO_SHUTDOWN_MINUTES', '30'))

def in_allowed_channel():
    async def predicate(ctx):
        if ctx.channel.id != ALLOWED_CHANNEL_ID:
            channel = ctx.guild.get_channel(ALLOWED_CHANNEL_ID)
            if channel:
                await ctx.respond(f"This command can only be used in {channel.mention}", ephemeral=True)
            else:
                await ctx.respond("This command can only be used in the designated channel.", ephemeral=True)
            return False
        return True
    return commands.check(predicate)

class MinecraftServerManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.host = os.getenv('CRAFTY_HOST', 'localhost')
        self.port = int(os.getenv('CRAFTY_PORT', '8443'))
        self.ssl = os.getenv('CRAFTY_SSL', 'true').lower() == 'true'
        self.token = os.getenv('CRAFTY_API_KEY')
        self.last_player_time = {}
        
        if not self.token:
            raise ValueError("CRAFTY_API_KEY not found in environment variables")
        
        # Log configuration on startup
        logger.info(f"Initialized with host: {self.host}:{self.port}")
        logger.info(f"SSL enabled: {self.ssl}")
        logger.info(f"Available servers: {list(SERVERS.keys())}")
        logger.info(f"Commands restricted to channel ID: {ALLOWED_CHANNEL_ID}")
        logger.info(f"Auto-shutdown after {AUTO_SHUTDOWN_MINUTES} minutes of inactivity")
        
        # Start the background task
        self.check_inactive_servers.start()

    async def make_request(self, path: str, method: str = "GET", data: dict = None) -> dict:
        """Make a request to the Crafty API"""
        url = f'http{"s" if self.ssl else ""}://{self.host}:{self.port}/api/v2{path if path.startswith("/") else "/" + path}'
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        logger.debug(f"Making {method} request to: {url}")
        
        # SSL context for self-signed certificates
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                async with session.request(method, url, headers=headers, json=data) as response:
                    text = await response.text()
                    logger.debug(f"API Response ({response.status}): {text}")
                    
                    response_data = json.loads(text)
                    if response_data.get("status") != "ok":
                        raise Exception(response_data.get("error", "Unknown error"))
                    
                    return response_data.get("data", {})
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise

    async def server_action(self, server_id: str, action: ServerActions) -> bool:
        """Execute a server action"""
        try:
            await self.make_request(
                path=f'/servers/{server_id}/action/{action.value}',
                method="POST"
            )
            return True
        except Exception:
            return False

    async def get_server_stats(self, server_id: str) -> dict:
        """Get server statistics"""
        return await self.make_request(path=f'/servers/{server_id}/stats')

    @commands.slash_command(
        name="start",
        description="Start a Minecraft server"
    )
    @in_allowed_channel()
    async def start(self, ctx, servername: discord.Option(str, "The server to start", choices=SERVERS.keys())):
        await ctx.defer()
        
        try:
            server_id = SERVERS[servername]
            logger.info(f"Starting server {servername} ({server_id})")
            
            # Check if server is already running
            status = await self.get_server_stats(server_id)
            if status.get("running", False):
                await ctx.respond(f"Server {servername} is already running!")
                return
            
            # Start the server
            success = await self.server_action(server_id, ServerActions.START_SERVER)
            if success:
                await ctx.respond(f"Starting server {servername}...")
            else:
                await ctx.respond(f"Failed to start server {servername}.")
            
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            await ctx.respond(f"Error starting server: {str(e)}")

    @commands.slash_command(
        name="status",
        description="Check the status of a Minecraft server"
    )
    @in_allowed_channel()
    async def status(self, ctx, servername: discord.Option(str, "The server to check", choices=SERVERS.keys())):
        await ctx.defer()
        
        try:
            server_id = SERVERS[servername]
            status = await self.get_server_stats(server_id)
            
            is_running = status.get("running", False)
            player_count = status.get("player_count", 0)
            
            await ctx.respond(
                f"Server: {servername}\n"
                f"Status: {'🟢 Running' if is_running else '🔴 Stopped'}\n"
                f"Players online: {player_count}"
            )
            
        except Exception as e:
            logger.error(f"Error checking status: {e}")
            await ctx.respond(f"Error checking server status: {str(e)}")

    @tasks.loop(minutes=5)
    async def check_inactive_servers(self):
        """Check for inactive servers and shut them down if needed"""
        try:
            for server_name, server_id in SERVERS.items():
                logger.debug(f"Checking activity for server: {server_name}")
                try:
                    status = await self.get_server_stats(server_id)
                    
                    if status.get("running", False):
                        player_count = status.get("player_count", 0)
                        
                        if player_count == 0:
                            # If no players, record or update last empty time
                            if server_id not in self.last_player_time:
                                logger.info(f"Server {server_name} has become empty, starting inactive timer")
                                self.last_player_time[server_id] = datetime.now()
                            elif datetime.now() - self.last_player_time[server_id] > timedelta(minutes=AUTO_SHUTDOWN_MINUTES):
                                logger.info(f"Server {server_name} has been inactive for {AUTO_SHUTDOWN_MINUTES} minutes, initiating shutdown")
                                
                                # Backup then stop
                                backup_success = await self.server_action(server_id, ServerActions.BACKUP_SERVER)
                                if backup_success:
                                    logger.info(f"Backup completed for {server_name}")
                                    
                                    stop_success = await self.server_action(server_id, ServerActions.STOP_SERVER)
                                    if stop_success:
                                        logger.info(f"Successfully stopped {server_name}")
                                        # Send notification to Discord
                                        channel = self.bot.get_channel(ALLOWED_CHANNEL_ID)
                                        if channel:
                                            await channel.send(
                                                f"Server {server_name} has been automatically stopped after "
                                                f"{AUTO_SHUTDOWN_MINUTES} minutes of inactivity. "
                                                f"Use `/start {server_name}` to start it again."
                                            )
                                    
                                # Reset the timer
                                self.last_player_time.pop(server_id, None)
                        else:
                            # Server has players, reset the timer
                            if server_id in self.last_player_time:
                                logger.info(f"Players detected on {server_name}, resetting inactive timer")
                                self.last_player_time.pop(server_id)
                                
                except Exception as e:
                    logger.error(f"Error checking server {server_name}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in check_inactive_servers task: {str(e)}")

    @check_inactive_servers.before_loop
    async def before_check_inactive_servers(self):
        """Wait until the bot is ready before starting the task"""
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(MinecraftServerManager(bot))
