# GDG Ulaanbaatar Tech News Bot 🤖

A professional Discord bot that automatically fetches the latest tech news from **The Verge** and translates them to **Mongolian** for the GDG Ulaanbaatar community.

## Features 🚀

- **📰 Automated News Fetching**: Checks The Verge RSS feed every 4 hours for latest tech news
- **🌍 Mongolian Translation**: Translates news titles and descriptions from English to Mongolian
- **🎯 Smart Tech Filtering**: Advanced filtering to ensure only technology-related content
- **🏢 Multi-Server Support**: Deploy across multiple Discord servers simultaneously
- **🎨 Professional Design**: Clean, branded embeds with GDG Ulaanbaatar theming (no emojis)
- **🔐 Robust Permission Handling**: Works gracefully even with limited Discord permissions
- **💬 Interactive Mentions**: Users can mention the bot to get latest news
- **🛡️ Error Recovery**: Intelligent fallbacks and comprehensive error handling

## Bot Commands 🎮

### User Commands

- **`!info`** - Show bot information and help
- **`!status`** - Check bot status and statistics
- **`!checkperms`** - Check bot permissions in current channel

### Admin Commands

- **`!news`** - Manually fetch and post latest news (requires Manage Messages permission)

### Mention Support

Users can interact with the bot naturally:

- `@GDG UB BOT шинэ мэдээ байна уу?` - Get latest tech news
- `@GDG UB BOT статус?` - Check bot status

## Setup Instructions 📋

### 1. Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name (e.g., "GDG News Bot")
3. Go to the "Bot" section
4. Click "Add Bot"
5. Copy the bot token (keep it secret!)
6. Under "Privileged Gateway Intents", enable:
   - Message Content Intent

### 2. Invite Bot to Your Server

1. In the Discord Developer Portal, go to "OAuth2" > "URL Generator"
2. Select scopes: `bot`
3. Select bot permissions:
   - Send Messages
   - Use Slash Commands
   - Embed Links
   - Read Message History
4. Copy the generated URL and open it to invite the bot to your server

### 3. Get Channel ID

1. Enable Developer Mode in Discord (User Settings > Advanced > Developer Mode)
2. Right-click on the channel where you want news posted
3. Click "Copy ID"

### 4. Install Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 5. Configure Environment

1. Copy `.env.example` to `.env`:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` file with your values:

   ```env
   # Discord Bot Configuration
   DISCORD_TOKEN=your_discord_bot_token_here
   DISCORD_CHANNEL_IDS=channel_id_1,channel_id_2,channel_id_3

   # Bot Settings
   CHECK_INTERVAL_HOURS=4
   STRICT_TECH_FILTER=true

   # Translation Settings
   TRANSLATE_TO_MONGOLIAN=true
   ```

   **Multi-Channel Setup**: Use comma-separated channel IDs to post to multiple channels/servers

### 6. Run the Bot

```bash
python bot.py
```

## Bot Commands 🎮

### User Commands

- **`!info`** - Show bot information and help
- **`!status`** - Check bot status and statistics
- **`!checkperms`** - Check bot permissions in current channel

### Admin Commands

- **`!news`** - Manually fetch and post latest news (requires Manage Messages permission)

### Mention Support

Users can interact with the bot naturally:

- `@GDG UB BOT шинэ мэдээ байна уу?` - Get latest tech news
- `@GDG UB BOT статус?` - Check bot status

## Configuration Options ⚙️

| Environment Variable     | Description                       | Default  |
| ------------------------ | --------------------------------- | -------- |
| `DISCORD_TOKEN`          | Your Discord bot token            | Required |
| `DISCORD_CHANNEL_IDS`    | Comma-separated channel IDs       | Required |
| `CHECK_INTERVAL_HOURS`   | Hours between news checks         | 4        |
| `STRICT_TECH_FILTER`     | Enable strict tech news filtering | true     |
| `TRANSLATE_TO_MONGOLIAN` | Enable Mongolian translation      | true     |

### Multi-Server Deployment

- **Single Channel**: `DISCORD_CHANNEL_IDS=123456789`
- **Multiple Channels**: `DISCORD_CHANNEL_IDS=123456789,987654321,555666777`
- **Cross-Server**: Bot can post to channels across different Discord servers

## How It Works 🔄

1. **📡 RSS Monitoring**: Bot checks The Verge RSS feed periodically
2. **🎯 Smart Tech Filtering**: Advanced keyword analysis ensures only tech news is posted
3. **🌍 Translation**: Uses Google Translate to convert English to Mongolian
4. **🎨 Professional Posting**: Creates clean, branded embeds with GDG theming
5. **🔍 Original Reference**: Includes original English titles for accuracy
6. **🛡️ Error Handling**: Graceful fallbacks for permission issues and server restrictions

## Architecture 🏗️

The bot uses a **professional modular architecture**:

- **`NewsService`**: Handles RSS feed parsing and tech content filtering
- **`TranslationService`**: Manages English to Mongolian translation
- **`GDGNewsBot`**: Main bot class with permission-aware messaging
- **Multi-Channel Support**: Intelligent routing for multiple Discord servers
- **Error Recovery**: Comprehensive exception handling and fallback mechanisms

## Deployment Options 🚀

### Option 1: Local Development

- Run on your computer for testing
- Stop the script to stop the bot

### Option 2: VPS/Cloud Server

- Deploy to a VPS (DigitalOcean, Linode, etc.)
- Use `screen` or `tmux` to keep it running
- Set up systemd service for auto-restart

### Option 3: Heroku

- Create a `Procfile`:
  ```
  worker: python bot.py
  ```
- Deploy to Heroku with hobby dyno

### Option 4: Railway/Render

- Connect your GitHub repo
- Set environment variables in the dashboard
- Deploy automatically

## Translation Notes 🌐

- Uses Google Translate (free tier) for translation
- For production use, consider Google Cloud Translation API for better reliability
- Mongolian language code: `mn`
- Translations include both traditional and modern Mongolian terms

## Troubleshooting 🛠️

### Common Issues:

1. **Bot not responding**:

   - Check if bot token is correct in `.env` file
   - Ensure bot has necessary permissions (use `!checkperms` command)
   - Verify bot is online in Discord server members list

2. **Permission errors (403 Forbidden)**:

   - Run `!checkperms` to diagnose permission issues
   - Ensure bot has "Send Messages" and "Embed Links" permissions
   - Bot will fall back to plain text if embed permissions are missing

3. **No news posted**:

   - Verify channel IDs are correct in `.env` file
   - Check if tech filter is too strict (set `STRICT_TECH_FILTER=false`)
   - Review logs for RSS feed accessibility issues

4. **Translation errors**:

   - Google Translate has rate limits (bot includes retry logic)
   - Check internet connectivity
   - Set `TRANSLATE_TO_MONGOLIAN=false` to disable translation temporarily

5. **Multi-channel issues**:
   - Ensure bot is invited to all target servers
   - Check that channel IDs are comma-separated without spaces
   - Bot will skip channels it cannot access and continue with others

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support 💬

For questions or support:

- Open an issue on GitHub
- Contact GDG Ulaanbaatar organizers
- Join the community Discord server

---

Made with ❤️ for the GDG Ulaanbaatar community
