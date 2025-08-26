# 🆓 Render.com FREE TIER Deployment Guide

## ✅ Free Tier Solution

Since Render.com's free tier only supports **Web Services** (Background Workers require paid plans), here's how to deploy your Discord bot as a Web Service:

## 🚀 Deployment Steps

### 1. Update Your Render.com Service

1. **Go to your Render.com dashboard**
2. **Select your existing service**
3. **Update the Start Command**:
   ```
   python3 web_server.py
   ```
4. **Redeploy**

### 2. Environment Variables (same as before)

```
DISCORD_TOKEN = your_discord_bot_token
DISCORD_CHANNEL_IDS = 1408792635262505031,1408772588137611347
NEWS_CHECK_INTERVAL_HOURS = 4
MAX_NEWS_PER_POST = 3
STRICT_TECH_FILTER = true
TARGET_LANGUAGE = mn
```

## 🔧 How It Works

**Free Tier Web Service** = **Discord Bot** + **Health Check Server**

- ✅ **Discord bot runs in background thread**
- ✅ **Web server satisfies port binding requirement**
- ✅ **Health check endpoints available**
- ✅ **No additional costs**

## 📊 Monitoring Endpoints

Once deployed, you can monitor your bot:

- **Health Check**: `https://your-app.onrender.com/health`
- **Bot Status**: `https://your-app.onrender.com/status`

## ✅ Expected Logs

```
🚀 Starting GDG News Bot - FREE TIER DEPLOYMENT
==========================================================
📋 Deployment: Render.com Web Service (Free Tier)
🤖 Bot: Discord Bot + Web Health Check
==========================================================
🔄 Starting Discord bot in background thread...
🌐 Starting health server on port 10000...
✅ Health server started on port 10000
✅ Both services started successfully!
🔄 Services running continuously...
📡 Monitor at: https://your-app.onrender.com/health
```

## 🎯 Benefits

- ✅ **100% Free** - Uses Render.com free Web Service
- ✅ **Discord Bot Works** - Your bot functionality is preserved
- ✅ **Health Monitoring** - Web endpoints for status checking
- ✅ **Port Compliance** - Satisfies Render.com port requirements
- ✅ **Simple Setup** - Just update start command and redeploy

## 🔄 Next Steps

1. **Update Start Command** to `python3 web_server.py`
2. **Redeploy** your service
3. **Monitor** at your app URL/health
4. **Test Discord bot** (should work same as before)

Your bot will work exactly the same in Discord, but now it also has a web interface for monitoring! 🤖✅
