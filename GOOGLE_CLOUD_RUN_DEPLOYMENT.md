# Google Cloud Run Deployment Guide

## Why Google Cloud Run is Perfect for Discord Bots

### ✅ Advantages over Render Free Tier

1. **No Sleep Issues**: Cloud Run doesn't put services to sleep like Render free tier
2. **Better Free Tier**: 2 million requests/month, 400,000 GB-seconds compute time
3. **Auto-scaling**: Scales to zero when not in use, but wakes up instantly
4. **Global Distribution**: Better latency worldwide
5. **Container-based**: More reliable and consistent deployments
6. **No Port Binding Requirements**: Can run background services without web endpoints

### 🎯 Perfect for Discord Bots

- **Always-on capability** without keep-alive hacks
- **Instant cold starts** (< 1 second)
- **Built-in logging** and monitoring
- **Automatic HTTPS** and SSL certificates
- **Environment variable management**

## Deployment Steps

### 1. Prepare Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Cloud Run requirement)
EXPOSE 8080

# Run the bot directly (no web server wrapper needed)
CMD ["python", "bot.py"]
```

### 2. Update bot.py for Cloud Run

```python
# Add at the top of bot.py
import os
from aiohttp import web
import threading

# Add simple health endpoint for Cloud Run
async def health_check(request):
    return web.json_response({"status": "healthy", "service": "GDG News Bot"})

async def start_health_server():
    """Start minimal health server for Cloud Run"""
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)

    port = int(os.environ.get('PORT', 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Health server running on port {port}")

# In main() function, before bot.run():
async def main():
    # Start health server in background
    await start_health_server()

    # Start bot
    await bot.start(os.getenv('DISCORD_TOKEN'))
```

### 3. Create cloudbuild.yaml (Optional - for CI/CD)

```yaml
steps:
  - name: "gcr.io/cloud-builders/docker"
    args: ["build", "-t", "gcr.io/$PROJECT_ID/gdg-news-bot", "."]
  - name: "gcr.io/cloud-builders/docker"
    args: ["push", "gcr.io/$PROJECT_ID/gdg-news-bot"]
  - name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
    entrypoint: "gcloud"
    args:
      - "run"
      - "deploy"
      - "gdg-news-bot"
      - "--image"
      - "gcr.io/$PROJECT_ID/gdg-news-bot"
      - "--region"
      - "us-central1"
      - "--platform"
      - "managed"
      - "--allow-unauthenticated"
```

## Deployment Commands

### Option 1: Using gcloud CLI

```bash
# 1. Install Google Cloud CLI
# Download from: https://cloud.google.com/sdk/docs/install

# 2. Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 3. Build and deploy
gcloud run deploy gdg-news-bot \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars DISCORD_TOKEN=your_token_here

# 4. Set environment variables
gcloud run services update gdg-news-bot \
  --region us-central1 \
  --set-env-vars DISCORD_TOKEN=your_discord_token
```

### Option 2: Using Docker + Cloud Run

```bash
# 1. Build Docker image
docker build -t gcr.io/YOUR_PROJECT_ID/gdg-news-bot .

# 2. Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/gdg-news-bot

# 3. Deploy to Cloud Run
gcloud run deploy gdg-news-bot \
  --image gcr.io/YOUR_PROJECT_ID/gdg-news-bot \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated
```

## Cost Analysis

### Free Tier Limits (Monthly)

- **2,000,000 requests** (more than enough for Discord bot)
- **400,000 GB-seconds** of compute time
- **2 million CPU-seconds**
- **Egress**: 1GB to North America, 1GB worldwide

### Estimated Usage for Discord Bot

- **Requests**: ~50,000/month (health checks + Discord events)
- **Compute**: ~50 GB-seconds/month
- **Result**: **Completely FREE** for this use case

## Configuration for Discord Bot

### Environment Variables

```bash
DISCORD_TOKEN=your_discord_bot_token
PORT=8080  # Cloud Run requirement
```

### Service Configuration

- **CPU**: 1 vCPU (default)
- **Memory**: 512Mi (sufficient for Discord bot)
- **Concurrency**: 1 (Discord bots should not be concurrent)
- **Timeout**: 3600 seconds (1 hour max)

## Migration from Current Setup

### Easy Migration Steps

1. **Keep current bot.py** - minimal changes needed
2. **Add simple Dockerfile** (5 lines)
3. **Deploy to Cloud Run** (one command)
4. **Update environment variables**
5. **Delete Render service** and web_server.py

### No More Worries About

- ❌ Service sleeping
- ❌ Keep-alive pings
- ❌ Complex web server wrappers
- ❌ Port binding requirements
- ❌ 15-minute inactivity limits

## Monitoring and Logs

### Cloud Console Features

- **Real-time logs** with filtering
- **Performance metrics** (CPU, memory, requests)
- **Error tracking** and alerting
- **Automatic restarts** on crashes
- **Health monitoring**

### Log Commands

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Stream logs
gcloud logging tail "resource.type=cloud_run_revision"
```

## Recommendation

🎯 **Switch to Google Cloud Run immediately!**

**Benefits for your use case:**

1. **No more sleep issues** - runs 24/7 reliably
2. **Better free tier** - won't hit limits
3. **Simpler code** - remove web_server.py complexity
4. **Better monitoring** - professional logging and metrics
5. **Future-proof** - can scale if needed

**Migration effort:** ~30 minutes
**Downtime:** ~5 minutes
**Cost:** $0 (within free tier)
