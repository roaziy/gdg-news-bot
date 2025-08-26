#!/usr/bin/env python3
"""
Simple web server for Render.com deployment
Runs alongside the Discord bot to satisfy port binding requirements
"""
import os
import asyncio
import threading
from aiohttp import web
from datetime import datetime
import json

# Import the bot
from bot import GDGNewsBot

class HealthServer:
    """Simple health check server for Render.com"""
    
    def __init__(self, port=10000):
        self.port = port
        self.bot_instance = None
        self.start_time = datetime.now()
    
    async def health_check(self, request):
        """Health check endpoint"""
        status = {
            "status": "healthy",
            "service": "GDG News Bot",
            "uptime": str(datetime.now() - self.start_time),
            "timestamp": datetime.now().isoformat(),
            "bot_connected": self.bot_instance is not None and hasattr(self.bot_instance, 'bot') and self.bot_instance.bot.is_ready() if self.bot_instance else False
        }
        return web.json_response(status)
    
    async def bot_info(self, request):
        """Bot information endpoint"""
        if self.bot_instance and hasattr(self.bot_instance, 'bot') and self.bot_instance.bot.is_ready():
            info = {
                "bot_name": str(self.bot_instance.bot.user),
                "guild_count": len(self.bot_instance.bot.guilds),
                "latency": round(self.bot_instance.bot.latency * 1000, 2),
                "status": "connected"
            }
        else:
            info = {
                "status": "starting or disconnected"
            }
        
        return web.json_response(info)
    
    async def start_server(self):
        """Start the web server"""
        app = web.Application()
        
        # Add routes
        app.router.add_get('/', self.health_check)
        app.router.add_get('/health', self.health_check)
        app.router.add_get('/status', self.bot_info)
        
        # Start server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        print(f"✅ Health server started on port {self.port}")
        print(f"🌐 Health check: http://localhost:{self.port}/health")
        
    def run_bot_in_thread(self):
        """Run the Discord bot in a separate thread"""
        def bot_runner():
            try:
                self.bot_instance = GDGNewsBot()
                self.bot_instance.run()
            except Exception as e:
                print(f"❌ Bot error: {e}")
        
        bot_thread = threading.Thread(target=bot_runner, daemon=True)
        bot_thread.start()
        return bot_thread

async def main():
    """Main function to run both web server and Discord bot"""
    # Get port from environment (Render.com sets this)
    port = int(os.environ.get('PORT', 10000))
    
    print("🚀 Starting GDG News Bot with Web Server")
    print("=" * 50)
    
    # Create health server
    health_server = HealthServer(port)
    
    # Start Discord bot in background thread
    print("🤖 Starting Discord bot...")
    bot_thread = health_server.run_bot_in_thread()
    
    # Start web server
    print(f"🌐 Starting health server on port {port}...")
    await health_server.start_server()
    
    print("✅ Both services started successfully!")
    print(f"📡 Health check available at: http://localhost:{port}/health")
    print("🔄 Bot will run continuously...")
    
    # Keep the server running
    try:
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour, then check again
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")

if __name__ == "__main__":
    asyncio.run(main())
