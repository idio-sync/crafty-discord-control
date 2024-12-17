# Minecraft Server Controller via Discord

A Discord bot that manages Minecraft servers through the Crafty Controller API. Features include starting servers, checking status, and automatic shutdown of inactive servers. This is mainly for small servers hosted at home for a few friends.

## Features

- `/start [servername]` - Start a Minecraft server
- `/status [servername]` - Check server status
- Automatic server shutdown after configurable period of inactivity
- Automatic backup before shutdown
- Channel-specific command restrictions
- Discord notifications for auto-shutdown events

## Prerequisites

- Python 3.10 or higher
- Crafty Controller v2 instance
- Discord Bot Token
- Docker (optional)

## Installation

### Option 1: Docker

1. Pull the image:
```bash
docker pull idio-sync000/crafty-discord-control:latest
```

2. Run the container:
```bash
docker run -d \
  --name crafty-discord-control \
  -e DISCORD_TOKEN=your_token \
  -e DISCORD_GUILD_ID=your_guild_id \
  -e DISCORD_CHANNEL_ID=your_channel_id \
  -e CRAFTY_HOST=your_host \
  -e CRAFTY_PORT=your_port \
  -e CRAFTY_SSL=true \
  -e CRAFTY_API_KEY=your_key \
  -e MINECRAFT_SERVERS=survival:your-uuid \
  -e AUTO_SHUTDOWN_MINUTES=30 \
  idio-sync000/crafty-discord-control:latest
```

### Option 2: Manual Installation

1. Clone the repository

2. Install dependencies
`pip install -r requirements.txt`

4. Create a `.env` file with your configuration:
```env
# Discord Bot Configuration
DISCORD_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=your_guild_id
DISCORD_CHANNEL_ID=your_channel_id

# Crafty Controller Configuration
CRAFTY_HOST=192.168.50.137
CRAFTY_PORT=8443
CRAFTY_SSL=true
CRAFTY_API_KEY=your_api_key

# Server Configuration (format: name:uuid,name2:uuid2)
MINECRAFT_SERVERS=survival:6db0b699-8e23-40fd-aeec-5adf6f59e1e0

# Auto-shutdown configuration (in minutes)
AUTO_SHUTDOWN_MINUTES=30
```

4. Run the bot:
```bash
python bot.py
```

## Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the Bot section and create a bot
4. Enable these Privileged Gateway Intents:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent
5. Copy the bot token and add it to your `.env` file
6. Generate an invite link with these permissions:
   - Send Messages
   - Use Slash Commands
   - View Channels
7. Invite the bot to your server

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| DISCORD_TOKEN | Your Discord bot token | `NzkyNzE1NDU...` |
| DISCORD_GUILD_ID | Your Discord server ID | `123456789` |
| DISCORD_CHANNEL_ID | Channel ID where commands are allowed | `123456789` |
| CRAFTY_HOST | Crafty Controller host | `192.168.1.100` |
| CRAFTY_PORT | Crafty Controller port | `8443` |
| CRAFTY_SSL | Use SSL for Crafty Controller | `true` |
| CRAFTY_API_KEY | Your Crafty Controller API key | `your-api-key` |
| MINECRAFT_SERVERS | Server name:UUID pairs | `survival:uuid,creative:uuid2` |
| AUTO_SHUTDOWN_MINUTES | Minutes before auto-shutdown | `30` |

## Acknowledgments

- [Crafty Controller](https://craftycontrol.com/) for the server management API
- [Pycord](https://docs.pycord.dev/) for the Discord bot framework
