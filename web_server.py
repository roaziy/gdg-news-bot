#!/usr/bin/env python3
"""
Simple web server for Render.com deployment
Runs alongside the Discord bot to satisfy port binding requirements
"""
import os
import asyncio
import logging
from aiohttp import web
from datetime import datetime
import json

# Import the main function from bot
from bot import main as bot_main

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthServer:
    """Simple health check server for Render.com"""
    
    def __init__(self, port=10000):
        self.port = port
        self.start_time = datetime.now()
        self.bot_status = "starting"
    
    async def health_check(self, request):
        """Health check endpoint"""
        status = {
            "status": "healthy",
            "service": "GDG News Bot",
            "uptime": str(datetime.now() - self.start_time),
            "timestamp": datetime.now().isoformat(),
            "bot_status": self.bot_status,
            "deployment": "render.com web service"
        }
        return web.json_response(status)
    
    async def bot_info(self, request):
        """Bot information endpoint"""
        info = {
            "service": "GDG Ulaanbaatar Tech News Bot",
            "version": "2.0",
            "features": [
                "Mongolian translation",
                "Tech news filtering", 
                "Multi-server support",
                "Automatic scheduling"
            ],
            "status": self.bot_status,
            "source": "The Verge RSS",
            "channels": "2 Discord servers configured"
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
        
        self.bot_status = "server_ready"
        logger.info(f"✅ Health server started on port {self.port}")
        logger.info(f"🌐 Health check: http://localhost:{self.port}/health")
        logger.info(f"📊 Bot info: http://localhost:{self.port}/status")

async def run_bot_async():
    """Run the Discord bot asynchronously"""
    logger.info("🤖 Starting Discord bot...")
    try:
        # Run the bot main function
        await asyncio.get_event_loop().run_in_executor(None, bot_main)
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")

async def main():
    """Main function to run both web server and Discord bot"""
    # Get port from environment (Render.com sets this)
    port = int(os.environ.get('PORT', 10000))
    
    logger.info("🚀 Starting GDG News Bot with Web Server")
    logger.info("=" * 50)
    
    # Create health server
    health_server = HealthServer(port)
    
    # Start web server
    logger.info(f"🌐 Starting health server on port {port}...")
    await health_server.start_server()
    
    # Start Discord bot in background
    logger.info("🤖 Starting Discord bot in background...")
    bot_task = asyncio.create_task(run_bot_async())
    health_server.bot_status = "bot_starting"
    
    logger.info("✅ Both services started successfully!")
    logger.info(f"📡 Health check available at: http://localhost:{port}/health")
    logger.info("🔄 Bot will run continuously...")
    
    # Keep the server running
    try:
        await bot_task
    except Exception as e:
        logger.error(f"Error: {e}")
        
    # Keep web server alive
    try:
        while True:
            await asyncio.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down...")

if __name__ == "__main__":
    asyncio.run(main())
