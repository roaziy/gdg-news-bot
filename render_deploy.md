# Render.com Deployment Guide

## 🚀 Two Deployment Options

### Option 1: Background Worker (Recommended)

**Best for**: Discord bots that don't need web interface

1. **Create Background Worker on Render.com**:

   - Go to https://render.com/dashboard
   - Click "New +" → "Background Worker"
   - Connect repository: `roaziy/gdg-news-bot`
   - **Name**: `gdg-news-bot`
   - **Start Command**: `python3 bot.py`

2. **Set Environment Variables**:

   ```
   DISCORD_TOKEN = your_discord_bot_token
   DISCORD_CHANNEL_IDS = 1408792635262505031,1408772588137611347
   NEWS_CHECK_INTERVAL_HOURS = 4
   MAX_NEWS_PER_POST = 3
   STRICT_TECH_FILTER = true
   TARGET_LANGUAGE = mn
   ```

3. **Deploy**: Click "Create Background Worker"

### Option 2: Web Service (With Health Check)

**Best for**: If you want a web interface or health monitoring

1. **Create Web Service on Render.com**:

   - Go to https://render.com/dashboard
   - Click "New +" → "Web Service"
   - Connect repository: `roaziy/gdg-news-bot`
   - **Name**: `gdg-news-bot`
   - **Start Command**: `python3 web_server.py`

2. **Set Environment Variables** (same as above)

3. **Deploy**: Click "Create Web Service"

4. **Access Health Check**: `https://your-app.onrender.com/health`

## 🔧 Files Created

- `web_server.py` - Web server wrapper for Web Service deployment
- `render_deploy.md` - This deployment guide

## ✅ Expected Results

**Background Worker**: Bot runs silently, posts to Discord channels
**Web Service**: Bot runs + health check endpoint available

Both options will:

- ✅ Connect to Discord
- ✅ Post tech news every 4 hours
- ✅ Translate to Mongolian
- ✅ Handle multiple channels
- ✅ No more deprecation warnings
- ✅ No port binding errors

## 🛠️ Current Bot Status

Your bot is working perfectly! The only issue was deployment type mismatch.

Choose **Background Worker** for simplest deployment.
