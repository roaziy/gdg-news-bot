# GDG Ulaanbaatar Tech News Bot 🤖

A Discord bot that automatically fetches the latest tech news from **The Verge** and translates them to **Mongolian** for the GDG Ulaanbaatar community.

## Features 🚀

- **Automated News Fetching**: Checks The Verge RSS feed every 4 hours for latest tech news
- **Mongolian Translation**: Translates news titles and descriptions from English to Mongolian
- **Smart Filtering**: Only posts news from the last 24 hours to avoid spam
- **Rich Embeds**: Beautiful Discord embeds with original titles for reference
- **Admin Commands**: Test and status commands for server administrators

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
   DISCORD_TOKEN=your_discord_bot_token_here
   DISCORD_CHANNEL_ID=your_channel_id_here
   NEWS_CHECK_INTERVAL_HOURS=4
   MAX_NEWS_PER_POST=3
   TARGET_LANGUAGE=mn
   ```

### 6. Run the Bot

```bash
python bot.py
```

## Bot Commands 🎮

- `!test_news` - Manually fetch and post latest news (Admin only)
- `!news_status` - Check bot status and last update time

## Configuration Options ⚙️

| Environment Variable        | Description                          | Default        |
| --------------------------- | ------------------------------------ | -------------- |
| `DISCORD_TOKEN`             | Your Discord bot token               | Required       |
| `DISCORD_CHANNEL_ID`        | Channel ID where news will be posted | Required       |
| `NEWS_CHECK_INTERVAL_HOURS` | Hours between news checks            | 4              |
| `MAX_NEWS_PER_POST`         | Maximum articles per update          | 3              |
| `TARGET_LANGUAGE`           | Translation target language code     | mn (Mongolian) |

## How It Works 🔄

1. **RSS Monitoring**: Bot checks The Verge RSS feed periodically
2. **Content Filtering**: Only processes articles from the last 24 hours
3. **Translation**: Uses Google Translate to convert English to Mongolian
4. **Discord Posting**: Creates rich embeds with translated content
5. **Original Reference**: Includes original English titles for accuracy

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

   - Check if bot token is correct
   - Ensure bot has necessary permissions
   - Check if bot is online in Discord

2. **No news posted**:

   - Verify channel ID is correct
   - Check RSS feed accessibility
   - Review logs for error messages

3. **Translation errors**:

   - Google Translate has rate limits
   - Consider adding retry logic
   - Check internet connectivity

4. **Import errors**:
   - Ensure all dependencies are installed
   - Activate virtual environment
   - Run `pip install -r requirements.txt`

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License 📄

This project is open source and available under the [MIT License](LICENSE).

## Support 💬

For questions or support:

- Open an issue on GitHub
- Contact GDG Ulaanbaatar organizers
- Join the community Discord server

---

Made with ❤️ for the GDG Ulaanbaatar community
