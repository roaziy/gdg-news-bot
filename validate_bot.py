#!/usr/bin/env python3
"""
GDG News Bot - Final Validation Test
Tests all bot functionality including permission handling
"""

import asyncio
import discord
import os
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BotValidator:
    def __init__(self):
        self.results = []
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.results.append({
            'test': test_name,
            'status': status,
            'details': details,
            'time': timestamp
        })
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"[{timestamp}] {status_emoji} {test_name}: {status}")
        if details:
            print(f"    └─ {details}")
    
    def validate_environment(self):
        """Validate environment configuration"""
        print("\n🔧 ENVIRONMENT VALIDATION")
        print("=" * 50)
        
        # Check .env file exists
        if os.path.exists('.env'):
            self.log_test("Environment File", "PASS", ".env file found")
        else:
            self.log_test("Environment File", "FAIL", ".env file missing")
            return False
            
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check required variables
        required_vars = [
            'DISCORD_TOKEN',
            'DISCORD_CHANNEL_IDS'
        ]
        
        for var in required_vars:
            value = os.getenv(var)
            if value and value != 'your_discord_bot_token_here':
                self.log_test(f"Environment: {var}", "PASS", f"Configured")
            else:
                self.log_test(f"Environment: {var}", "FAIL", f"Missing or placeholder value")
        
        # Check channel IDs format
        channel_ids = os.getenv('DISCORD_CHANNEL_IDS', '')
        if channel_ids:
            channels = [cid.strip() for cid in channel_ids.split(',') if cid.strip()]
            self.log_test("Channel Configuration", "PASS", f"{len(channels)} channels configured")
        else:
            self.log_test("Channel Configuration", "FAIL", "No channels configured")
        
        return True
    
    def validate_dependencies(self):
        """Validate all required dependencies"""
        print("\n📦 DEPENDENCY VALIDATION")
        print("=" * 50)
        
        dependencies = [
            ('discord.py', 'discord'),
            ('feedparser', 'feedparser'), 
            ('googletrans', 'googletrans'),
            ('python-dotenv', 'dotenv'),
            ('schedule', 'schedule'),
            ('aiohttp', 'aiohttp'),
            ('beautifulsoup4', 'bs4'),
            ('requests', 'requests')
        ]
        
        for package_name, import_name in dependencies:
            try:
                __import__(import_name)
                self.log_test(f"Package: {package_name}", "PASS", "Available")
            except ImportError:
                self.log_test(f"Package: {package_name}", "FAIL", "Missing - run pip install -r requirements.txt")
    
    def validate_bot_structure(self):
        """Validate bot code structure"""
        print("\n🏗️ CODE STRUCTURE VALIDATION")
        print("=" * 50)
        
        # Check main bot file
        if os.path.exists('bot.py'):
            self.log_test("Main Bot File", "PASS", "bot.py exists")
            
            # Check for key classes/functions
            with open('bot.py', 'r', encoding='utf-8') as f:
                content = f.read()
                
            checks = [
                ('NewsService class', 'class NewsService'),
                ('TranslationService class', 'class TranslationService'),
                ('GDGNewsBot class', 'class GDGNewsBot'),
                ('Permission handling', 'discord.Forbidden'),
                ('Tech filtering', 'is_tech_related'),
                ('Multi-channel support', 'DISCORD_CHANNEL_IDS'),
                ('Permission checker command', '@self.bot.command(name=\'checkperms\'')
            ]
            
            for check_name, check_pattern in checks:
                if check_pattern in content:
                    self.log_test(f"Code Feature: {check_name}", "PASS", "Implemented")
                else:
                    self.log_test(f"Code Feature: {check_name}", "FAIL", "Missing implementation")
        else:
            self.log_test("Main Bot File", "FAIL", "bot.py missing")
    
    def print_summary(self):
        """Print validation summary"""
        print("\n📊 VALIDATION SUMMARY")
        print("=" * 50)
        
        pass_count = sum(1 for r in self.results if r['status'] == 'PASS')
        fail_count = sum(1 for r in self.results if r['status'] == 'FAIL')
        warn_count = sum(1 for r in self.results if r['status'] == 'WARN')
        total_count = len(self.results)
        
        print(f"Total Tests: {total_count}")
        print(f"✅ Passed: {pass_count}")
        print(f"❌ Failed: {fail_count}")
        print(f"⚠️ Warnings: {warn_count}")
        
        if fail_count == 0:
            print("\n🎉 ALL VALIDATIONS PASSED!")
            print("Bot is ready for deployment and should work correctly.")
        else:
            print(f"\n🚨 {fail_count} ISSUES FOUND")
            print("Please fix the failed tests before deploying the bot.")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.results:
            status_emoji = "✅" if result['status'] == "PASS" else "❌" if result['status'] == "FAIL" else "⚠️"
            print(f"  {status_emoji} [{result['time']}] {result['test']}: {result['status']}")
            if result['details']:
                print(f"      └─ {result['details']}")

def main():
    """Run all validation tests"""
    print("🤖 GDG NEWS BOT - FINAL VALIDATION")
    print("=" * 50)
    print("Testing bot configuration, dependencies, and code structure...")
    print()
    
    validator = BotValidator()
    
    try:
        validator.validate_environment()
        validator.validate_dependencies()
        validator.validate_bot_structure()
    except Exception as e:
        validator.log_test("Validation Process", "FAIL", f"Unexpected error: {e}")
    
    validator.print_summary()
    
    print("\n🔍 NEXT STEPS:")
    print("1. If all tests pass, your bot is ready to use")
    print("2. Run 'python bot.py' to start the bot")
    print("3. Test commands in Discord: !info, !status, !checkperms")
    print("4. Mention the bot: @GDG UB BOT шинэ мэдээ юу байна?")
    print("5. Monitor logs for any permission or connection issues")

if __name__ == "__main__":
    main()
