#!/usr/bin/env python3
"""
Simple web server for Render.com FREE TIER deployment
Runs Discord bot alongside web server to satisfy port binding requirements
Includes keep-alive ping to prevent free tier sleeping
"""
import os
import asyncio
import logging
import threading
import aiohttp
from aiohttp import web
from datetime import datetime
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to track bot status
bot_status = {"status": "starting", "error": None, "connected": False}

class HealthServer:
    """Simple health check server for Render.com"""
    
    def __init__(self, port=10000):
        self.port = port
        self.start_time = datetime.now()
    
    async def health_check(self, request):
        """Health check endpoint"""
        status = {
            "status": "healthy",
            "service": "GDG News Bot",
            "uptime": str(datetime.now() - self.start_time),
            "timestamp": datetime.now().isoformat(),
            "bot_status": bot_status["status"],
            "bot_connected": bot_status["connected"],
            "deployment": "render.com free web service",
            "schedule": "Daily UTC 01:00",
            "sources": "The Verge + CNET",
            "error": bot_status["error"]
        }
        return web.json_response(status)
    
    async def bot_info(self, request):
        """Bot information endpoint"""
        info = {
            "service": "GDG Ulaanbaatar Tech News Bot",
            "version": "2.1",
            "features": [
                "Mongolian translation",
                "Tech news filtering", 
                "Multi-server support",
                "Daily UTC 01:00 scheduling",
                "Dual news sources"
            ],
            "status": bot_status["status"],
            "sources": "The Verge + CNET RSS",
            "schedule": "Daily at UTC 01:00 (UB 09:00)",
            "articles_per_day": "4 total (2 from each source)",
            "channels": "2 Discord servers configured",
            "free_tier": "Render.com Web Service"
        }
        return web.json_response(info)
    
    async def start_server(self):
        """Start the web server"""
        app = web.Application()
        
        # Add routes
        app.router.add_get('/', self.health_check)
        app.router.add_get('/health', self.health_check)
        app.router.add_get('/status', self.bot_info)
        app.router.add_get('/info', self.bot_info)
        
        # Start server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        logger.info(f"✅ Health server started on port {self.port}")
        logger.info(f"🌐 Health check: http://0.0.0.0:{self.port}/health")
        logger.info(f"📊 Bot info: http://0.0.0.0:{self.port}/status")

async def keep_alive_ping():
    """Ping self every 10 minutes to prevent Render free tier sleeping"""
    # Wait for server to fully start
    await asyncio.sleep(120)  # 2 minutes initial delay
    
    # Get the service URL from environment or build from port
    service_url = os.environ.get('RENDER_EXTERNAL_URL')
    if not service_url:
        # Fallback to localhost for testing or use your actual Render URL
        port = int(os.environ.get('PORT', 10000))
        service_url = f"http://localhost:{port}"
    
    logger.info(f"🔄 Keep-alive ping will target: {service_url}")
    
    while True:
        try:
            # Wait 10 minutes between pings (well under 15-minute sleep threshold)
            await asyncio.sleep(600)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f'{service_url}/health', timeout=30) as response:
                    if response.status == 200:
                        logger.info(f"✅ Keep-alive ping successful: {response.status}")
                    else:
                        logger.warning(f"⚠️ Keep-alive ping returned: {response.status}")
                        
        except asyncio.TimeoutError:
            logger.warning("⚠️ Keep-alive ping timeout - service may be sleeping")
        except aiohttp.ClientConnectorError as e:
            logger.warning(f"⚠️ Keep-alive ping connection error: {e}")
        except Exception as e:
            logger.error(f"❌ Keep-alive ping failed: {e}")
            
        # Small delay before next iteration to prevent rapid retries on error
        await asyncio.sleep(10)

def run_discord_bot():
    """Run Discord bot in a separate thread"""
    try:
        logger.info("🤖 Starting Discord bot in thread...")
        bot_status["status"] = "initializing"
        
        # Import and run the bot
        from bot import main as bot_main
        bot_status["status"] = "running"
        bot_status["connected"] = True
        bot_main()
        
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        bot_status["status"] = "error"
        bot_status["error"] = str(e)
        bot_status["connected"] = False

async def main():
    """Main function for Render.com FREE TIER"""
    # Get port from environment (Render.com sets this)
    port = int(os.environ.get('PORT', 10000))
    
    logger.info("🚀 Starting GDG News Bot - FREE TIER DEPLOYMENT")
    logger.info("=" * 60)
    logger.info("📋 Deployment: Render.com Web Service (Free Tier)")
    logger.info("🤖 Bot: Discord Bot + Web Health Check")
    logger.info("📅 Schedule: Daily at UTC 01:00 (UB 09:00)")
    logger.info("📰 Sources: The Verge + CNET (4 articles)")
    logger.info("=" * 60)
    
    # Start Discord bot in background thread
    logger.info("🔄 Starting Discord bot in background thread...")
    bot_thread = threading.Thread(target=run_discord_bot, daemon=True)
    bot_thread.start()
    
    # Give bot a moment to start
    await asyncio.sleep(2)
    
    # Create and start health server
    health_server = HealthServer(port)
    logger.info(f"🌐 Starting health server on port {port}...")
    await health_server.start_server()
    
    logger.info("✅ Both services started successfully!")
    logger.info("🔄 Services running continuously...")
    logger.info("📅 Bot posts daily at UTC 01:00 (UB 09:00)")
    logger.info(f"📡 Monitor at: https://your-app.onrender.com/health")
    
    # Start keep-alive ping task
    keep_alive_task = asyncio.create_task(keep_alive_ping())
    logger.info("⏰ Keep-alive ping task started")
    
    # Keep the web server alive forever
    try:
        while True:
            await asyncio.sleep(60)  # Keep alive check every minute
            logger.debug("Web server heartbeat...")
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down...")
        keep_alive_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
