# Migration Guide - v2.0 Updates

## 🚀 New Features

### 1. **Improved Tech News Filtering**

- Bot now filters out non-tech news from The Verge
- Only posts actual technology-related articles
- Configurable filtering via `STRICT_TECH_FILTER` setting

### 2. **Multi-Server Support**

- Can now post to multiple Discord channels/servers
- Support for comma-separated channel IDs
- Backward compatible with single channel setup

## 📝 Required .env File Updates

### **Option 1: Multiple Channels (Recommended)**

```env
# Discord Bot Configuration
DISCORD_TOKEN=your_bot_token_here

# Multiple channels - comma separated
DISCORD_CHANNEL_IDS=1234567890,9876543210,1111222233

# News Configuration
NEWS_CHECK_INTERVAL_HOURS=4
MAX_NEWS_PER_POST=3

# Tech News Filtering
STRICT_TECH_FILTER=true

# Translation Configuration
TARGET_LANGUAGE=mn
```

### **Option 2: Single Channel (Legacy)**

```env
# Discord Bot Configuration
DISCORD_TOKEN=your_bot_token_here

# Single channel (old format still works)
DISCORD_CHANNEL_ID=1234567890

# News Configuration
NEWS_CHECK_INTERVAL_HOURS=4
MAX_NEWS_PER_POST=3

# Tech News Filtering
STRICT_TECH_FILTER=true

# Translation Configuration
TARGET_LANGUAGE=mn
```

## ⚙️ Configuration Options

### **STRICT_TECH_FILTER**

- `true` (default): Only posts technology-related news
- `false`: Posts all news from The Verge (old behavior)

### **DISCORD_CHANNEL_IDS**

- Format: `channel_id1,channel_id2,channel_id3`
- Example: `1408772588137611347,1234567890123456789`
- Bot will post to ALL listed channels

## 🔧 How to Get Channel IDs for Multiple Servers

1. **Enable Developer Mode** in Discord
2. **For each server you want to add:**

   - Right-click the channel where you want news
   - Click "Copy ID"
   - Add to your comma-separated list

3. **Example for 3 servers:**
   ```env
   DISCORD_CHANNEL_IDS=1408772588137611347,9876543210123456789,1111222233445566777
   ```

## 📊 What Changed

### **Tech Filtering**

- **Before**: Posted all Verge articles (including politics, entertainment, etc.)
- **After**: Only posts tech-related articles (AI, programming, gadgets, etc.)

### **Multi-Server Support**

- **Before**: Could only post to one Discord channel
- **After**: Can post to multiple channels across different servers

### **Better Logging**

- Shows which channels articles were posted to
- Displays filtering status
- Better error handling for multiple channels

## 🛠️ Migration Steps

1. **Update your .env file** with new format
2. **Test the bot**: `python test_setup.py`
3. **Run the bot**: `python bot.py`
4. **Check logs** to confirm multi-channel posting

## 🔍 Tech Filter Keywords

The bot now filters for articles containing:

- **Companies**: Apple, Google, Microsoft, Meta, Tesla, etc.
- **Tech Terms**: AI, machine learning, blockchain, VR, AR, etc.
- **Development**: Programming, coding, API, cloud, etc.
- **Devices**: Smartphone, laptop, smartwatch, etc.
- **Gaming**: Console, Steam, PlayStation, etc.

And excludes:

- Politics, elections, government
- Sports, entertainment, movies
- Weather, climate (unless tech-related)
- General health, finance news

## ❓ Need Help?

If you have issues with migration:

1. Check your .env file format
2. Verify channel IDs are correct
3. Run `python test_setup.py`
4. Check bot logs for error messages
