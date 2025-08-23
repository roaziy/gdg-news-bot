"""
Test script to verify the Discord bot setup
Run this after setting up your .env file to test the bot connection
"""

import os
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands

# Load environment variables
load_dotenv()

async def test_bot_connection():
    """Test Discord bot connection"""
    token = os.getenv('DISCORD_TOKEN')
    channel_id = os.getenv('DISCORD_CHANNEL_ID')
    
    print("GDG News Bot - Connection Test")
    print("=" * 40)
    
    # Check environment variables
    if not token:
        print("DISCORD_TOKEN not found in .env file")
        return False
    
    if not channel_id:
        print("DISCORD_CHANNEL_ID not found in .env file")
        return False
    
    print("Environment variables loaded")
    print(f"Target Channel ID: {channel_id}")
    
    # Test bot connection
    try:
        intents = discord.Intents.default()
        intents.message_content = True
        bot = commands.Bot(command_prefix='!', intents=intents)
        
        @bot.event
        async def on_ready():
            print(f"Bot connected successfully as {bot.user}")
            print(f"Bot is in {len(bot.guilds)} servers:")
            for guild in bot.guilds:
                print(f"   - {guild.name} (ID: {guild.id})")
            
            # Test channel access
            channel = bot.get_channel(int(channel_id))
            if channel:
                print(f"Can access target channel: #{channel.name}")
                
                # Test sending a message
                try:
                    embed = discord.Embed(
                        title="Тест мессеж",
                        description="GDG News Bot холболт амжилттай!",
                        color=0x4285f4
                    )
                    await channel.send(embed=embed)
                    print("Test message sent successfully")
                except discord.Forbidden:
                    print("Bot doesn't have permission to send messages in this channel")
                except Exception as e:
                    print(f"Error sending test message: {e}")
            else:
                print(f"Cannot access channel with ID: {channel_id}")
                print("   Make sure the bot is in the server and has access to the channel")
            
            await bot.close()
        
        # Connect to Discord
        await bot.start(token)
        
    except discord.LoginFailure:
        print("Invalid Discord token")
        return False
    except Exception as e:
        print(f"Connection error: {e}")
        return False
    
    return True

def test_translation():
    """Test translation functionality"""
    print("\nTesting Translation")
    print("=" * 40)
    
    try:
        from googletrans import Translator
        translator = Translator()
        
        # Test translation
        test_text = "Google Developers Group Ulaanbaatar"
        result = translator.translate(test_text, dest='mn')
        
        print(f"Original: {test_text}")
        print(f"Translated: {result.text}")
        print("Translation test successful")
        return True
        
    except Exception as e:
        print(f"Translation error: {e}")
        return False

def test_news_feed():
    """Test news feed fetching"""
    print("\nTesting News Feed")
    print("=" * 40)
    
    try:
        import feedparser
        
        # Test The Verge RSS feed
        feed = feedparser.parse("https://www.theverge.com/rss/index.xml")
        
        if feed.entries:
            print(f"Successfully fetched {len(feed.entries)} articles")
            print(f"Latest article: {feed.entries[0].title}")
            return True
        else:
            print("No articles found in RSS feed")
            return False
            
    except Exception as e:
        print(f"RSS feed error: {e}")
        return False

async def main():
    """Run all tests"""
    print("Starting GDG News Bot Tests...\n")
    
    # Test 1: Translation
    translation_ok = test_translation()
    
    # Test 2: News Feed
    news_ok = test_news_feed()
    
    # Test 3: Discord Connection (only if .env exists)
    discord_ok = False
    if os.path.exists('.env'):
        discord_ok = await test_bot_connection()
    else:
        print("\nDiscord Bot Connection Test")
        print("=" * 40)
        print(".env file not found. Please:")
        print("   1. Copy .env.example to .env")
        print("   2. Add your Discord bot token and channel ID")
        print("   3. Run this test again")
    
    # Summary
    print("\nTest Summary")
    print("=" * 40)
    print(f"Translation: {'PASS' if translation_ok else 'FAIL'}")
    print(f"News Feed: {'PASS' if news_ok else 'FAIL'}")
    print(f"Discord Bot: {'PASS' if discord_ok else 'FAIL'}")
    
    if all([translation_ok, news_ok, discord_ok]):
        print("\nAll tests passed! Your bot is ready to run.")
        print("   Start the bot with: python bot.py")
    else:
        print("\nSome tests failed. Please check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
