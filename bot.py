import discord
from discord.ext import commands, tasks
import feedparser
import asyncio
import os
from datetime import datetime, timedelta, timezone
import json
from deep_translator import GoogleTranslator
from dotenv import load_dotenv
import logging
import aiohttp
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional

# Ulaanbaatar timezone (UTC+8)
ULAANBAATAR_TZ = timezone(timedelta(hours=8))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gdg_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NewsArticle:
    """Data class for news articles"""
    def __init__(self, title: str, description: str, link: str, published: datetime, author: str = "The Verge"):
        self.title = title
        self.description = description
        self.link = link
        self.published = published
        self.author = author

class TranslationService:
    """Handles text translation to Mongolian"""
    
    def __init__(self):
        self.max_chunk_size = 500
    
    async def translate_to_mongolian(self, text: str) -> str:
        """Translate text to Mongolian with chunking for long texts"""
        try:
            if len(text) <= self.max_chunk_size:
                translator = GoogleTranslator(source='en', target='mn')
                result = translator.translate(text)
                return result
            
            # Split text into sentences and translate in chunks
            sentences = text.split('. ')
            translated_chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk + sentence) < self.max_chunk_size:
                    current_chunk += sentence + ". "
                else:
                    if current_chunk:
                        translator = GoogleTranslator(source='en', target='mn')
                        result = translator.translate(current_chunk.strip())
                        translated_chunks.append(result)
                        current_chunk = sentence + ". "
                    else:
                        translator = GoogleTranslator(source='en', target='mn')
                        result = translator.translate(sentence)
                        translated_chunks.append(result)
            
            if current_chunk:
                translator = GoogleTranslator(source='en', target='mn')
                result = translator.translate(current_chunk.strip())
                translated_chunks.append(result)
            
            return " ".join(translated_chunks)
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return f"[Орчуулга амжилтгүй] {text}"

class NewsService:
    """Handles fetching and processing news from The Verge and CNET"""
    
    def __init__(self):
        # RSS feeds for both sources
        self.verge_rss_url = "https://www.theverge.com/rss/index.xml"
        self.cnet_rss_url = "https://www.cnet.com/rss/news/"
        self.last_check_file = 'last_check.json'
        self.strict_tech_filter = True  # Will be set by bot
    
    def clean_html(self, html_text: str) -> str:
        """Remove HTML tags from text"""
        try:
            soup = BeautifulSoup(html_text, 'html.parser')
            text = soup.get_text()
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        except Exception:
            return html_text
    
    def is_tech_news(self, title: str, description: str, categories: list = None) -> bool:
        """Enhanced filter to check if article is actually tech-related using RSS categories"""
        
        # Priority 1: Check RSS categories first (most reliable)
        if categories:
            category_names = [cat.lower() for cat in categories]
            
            # Core tech categories that strongly indicate tech content
            core_tech_categories = ['tech', 'ai', 'apple', 'google', 'microsoft', 'meta', 'intel', 'nvidia', 'amd', 'samsung', 'hardware', 'software', 'gadgets']
            
            # Check if article has core tech categories
            has_core_tech = any(cat in category_names for cat in core_tech_categories)
            
            # Strict exclusion categories - articles we never want
            strict_exclude_categories = [
                'entertainment', 'film', 'tv shows', 'streaming', 'games review',
                'sports', 'health', 'medical', 'climate', 'environment', 'culture', 
                'food', 'travel', 'lifestyle', 'speech'
            ]
            
            # Always exclude these categories
            for exclude_cat in strict_exclude_categories:
                if any(exclude_cat in cat for cat in category_names):
                    return False
            
            # For political/policy articles, only allow if they have strong tech focus
            if any(pol_cat in category_names for pol_cat in ['politics', 'policy']):
                # Must have core tech categories AND be about tech companies
                tech_companies = ['apple', 'google', 'microsoft', 'meta', 'intel', 'nvidia', 'amd', 'openai', 'tesla', 'amazon']
                has_tech_company = any(company in category_names for company in tech_companies)
                return has_core_tech and has_tech_company
            
            # Include if article has core tech categories
            if has_core_tech:
                return True
            
            # Special case: Gaming is tech if it's about gaming technology/industry (not reviews)
            if 'gaming' in category_names and 'games review' not in category_names:
                return True
        
        # Priority 2: Fallback to keyword analysis for articles without categories
        content = f"{title} {description}".lower()
        
        # Strong exclusion keywords for non-tech content
        exclude_keywords = [
            'movie', 'film', 'tv show', 'celebrity', 'entertainment industry',
            'sports', 'football', 'basketball', 'olympics', 'game review',
            'climate change', 'global warming', 'health crisis'
        ]
        
        # Check exclusion keywords first
        for keyword in exclude_keywords:
            if keyword in content:
                return False
        
        # Core tech keywords that strongly indicate tech content
        core_tech_keywords = [
            # Major tech companies
            'apple', 'google', 'microsoft', 'meta', 'amazon', 'tesla', 'nvidia', 
            'intel', 'amd', 'openai', 'anthropic', 'samsung', 'qualcomm',
            
            # Core technologies
            'artificial intelligence', 'machine learning', 'blockchain', 'cryptocurrency',
            'quantum computing', 'robotics', 'automation', 'cybersecurity',
            
            # Devices & hardware
            'smartphone', 'iphone', 'android', 'laptop', 'tablet', 'processor', 
            'chip', 'semiconductor', 'cpu', 'gpu', 'smartwatch', 'drone',
            
            # Software & platforms
            'software development', 'app store', 'operating system', 'cloud computing', 'api'
        ]
        
        # Check for core tech keywords
        tech_score = 0
        for keyword in core_tech_keywords:
            if keyword in content:
                tech_score += 1
        
        # Require at least 1 strong tech keyword match
        return tech_score > 0

    async def fetch_latest_articles(self, max_articles: int = 2) -> List[NewsArticle]:
        """Fetch latest tech news articles from The Verge and CNET"""
        try:
            all_articles = []
            
            # Fetch from The Verge (2 articles)
            verge_articles = await self._fetch_from_source(
                self.verge_rss_url, 
                "The Verge", 
                max_articles_per_source=2
            )
            all_articles.extend(verge_articles)
            
            # Fetch from CNET (2 articles)
            cnet_articles = await self._fetch_from_source(
                self.cnet_rss_url, 
                "CNET", 
                max_articles_per_source=2
            )
            all_articles.extend(cnet_articles)
            
            # Sort by publication date (newest first)
            all_articles.sort(key=lambda x: x.published, reverse=True)
            return all_articles
            
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return []
    
    async def _fetch_from_source(self, rss_url: str, source_name: str, max_articles_per_source: int = 2) -> List[NewsArticle]:
        """Fetch articles from a specific RSS source"""
        try:
            feed = feedparser.parse(rss_url)
            
            if not feed.entries:
                logger.warning(f"No entries found in {source_name} RSS feed")
                return []
            
            articles = []
            cutoff_time = datetime.now(ULAANBAATAR_TZ) - timedelta(hours=36)  # Extended to 36 hours for daily checks
            
            for entry in feed.entries[:20]:  # Check more articles to find tech ones
                try:
                    # Create timezone-aware datetime from RSS feed (UTC) and convert to Ulaanbaatar time
                    pub_date_utc = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    pub_date = pub_date_utc.astimezone(ULAANBAATAR_TZ)
                    
                    if pub_date > cutoff_time:
                        description = self.clean_html(entry.description)
                        if len(description) > 300:
                            description = description[:300] + "..."
                        
                        # Get categories if available
                        categories = []
                        if hasattr(entry, 'tags'):
                            categories = [tag.term for tag in entry.tags]
                        
                        # Filter for tech news only if strict filtering is enabled
                        if not self.strict_tech_filter or self.is_tech_news(entry.title, description, categories):
                            article = NewsArticle(
                                title=entry.title,
                                description=description,
                                link=entry.link,
                                published=pub_date,
                                author=source_name
                            )
                            articles.append(article)
                        
                        # Stop if we have enough articles from this source
                        if len(articles) >= max_articles_per_source:
                            break
                        
                except Exception as e:
                    logger.error(f"Error processing {source_name} article: {e}")
                    continue
            
            logger.info(f"Found {len(articles)} tech articles from {source_name}")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching news from {source_name}: {e}")
            return []
    
    def get_last_check_time(self) -> Optional[datetime]:
        """Get the last time news was checked"""
        try:
            if os.path.exists(self.last_check_file):
                with open(self.last_check_file, 'r') as f:
                    data = json.load(f)
                    return datetime.fromisoformat(data['last_check'])
        except Exception as e:
            logger.error(f"Error reading last check time: {e}")
        return None
    
    def save_last_check_time(self) -> None:
        """Save the current time as last check time"""
        try:
            with open(self.last_check_file, 'w') as f:
                json.dump({'last_check': datetime.now(ULAANBAATAR_TZ).isoformat()}, f)
        except Exception as e:
            logger.error(f"Error saving last check time: {e}")
class GDGNewsBot:
    """Main Discord bot class for GDG Ulaanbaatar news"""
    
    def __init__(self):
        # Configuration
        self.token = os.getenv('DISCORD_TOKEN')
        
        # Support multiple channels
        channel_ids_str = os.getenv('DISCORD_CHANNEL_IDS', '')
        single_channel = os.getenv('DISCORD_CHANNEL_ID', '0')
        
        if channel_ids_str:
            # Multiple channels support
            self.channel_ids = [int(cid.strip()) for cid in channel_ids_str.split(',') if cid.strip()]
        elif single_channel != '0':
            # Backward compatibility - single channel
            self.channel_ids = [int(single_channel)]
        else:
            self.channel_ids = []
        
        # Track recent mentions to prevent duplicate responses
        self.recent_mentions = {}  # Store message_id -> timestamp
        
        # Daily scheduled time for news posting (UTC 01:00)
        self.scheduled_hour = 1  # UTC hour (01:00)
        self.max_news_per_post = 4  # Total: 2 from Verge + 2 from CNET
        self.strict_tech_filter = os.getenv('STRICT_TECH_FILTER', 'true').lower() == 'true'
        
        # Services
        self.news_service = NewsService()
        self.news_service.strict_tech_filter = self.strict_tech_filter
        self.translation_service = TranslationService()
        
        # Discord bot setup
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        
        # Setup bot events and commands
        self.setup_events()
        self.setup_commands()
    
    def setup_events(self):
        """Setup Discord bot events"""
        
        @self.bot.event
        async def on_ready():
            logger.info(f'Bot {self.bot.user} connected to Discord')
            logger.info(f'Connected to {len(self.bot.guilds)} servers')
            
            if not self.news_check_task.is_running():
                self.news_check_task.start()
                logger.info('News checking task started')
        
        @self.bot.event
        async def on_message(message):
            # Ignore messages from the bot itself
            if message.author == self.bot.user:
                return
            
            # Check if bot is mentioned
            if self.bot.user in message.mentions:
                # Prevent duplicate responses (same message within 30 seconds)
                current_time = datetime.now(ULAANBAATAR_TZ)
                message_key = f"{message.id}_{message.channel.id}"
                
                if message_key in self.recent_mentions:
                    time_diff = current_time - self.recent_mentions[message_key]
                    if time_diff.total_seconds() < 30:  # 30 second cooldown
                        logger.debug(f"Ignoring duplicate mention within 30 seconds: {message_key}")
                        return
                
                # Clean old mentions (older than 5 minutes)
                cutoff_time = current_time - timedelta(minutes=5)
                self.recent_mentions = {k: v for k, v in self.recent_mentions.items() if v > cutoff_time}
                
                # Record this mention
                self.recent_mentions[message_key] = current_time
                
                content = message.content.lower()
                
                # Mongolian greetings and news requests
                mongolian_keywords = [
                    'шинэ мэдээ', 'мэдээ', 'medee', 'юу байна', 'сонин', 
                    'tech news', 'news', 'мэдээлэл'
                ]
                
                if any(keyword in content for keyword in mongolian_keywords):
                    await self.handle_news_request(message)
                else:
                    await self.handle_general_mention(message)
            
            # Process commands
            await self.bot.process_commands(message)
    
    async def handle_news_request(self, message):
        """Handle news request in Mongolian"""
        try:
            # Check if bot has permission to send embeds in this channel
            if not message.channel.permissions_for(message.guild.me).embed_links:
                await message.channel.send("Уучлаарай, энэ сувагт embed илгээх эрх надад байхгүй байна.")
                return
            
            # Create loading embed
            loading_embed = discord.Embed(
                title="🔍 Шинэ мэдээ хайж байна...",
                description="The Verge болон CNET-ээс хамгийн сүүлийн технологийн мэдээг авч байна",
                color=0xffa500
            )
            loading_embed.set_thumbnail(
                url="https://cdn.vox-cdn.com/uploads/chorus_asset/file/13668586/the_verge_logo.0.png"
            )
            
            try:
                loading_msg = await message.reply(embed=loading_embed)
            except discord.Forbidden:
                # Fallback: try to send without reply
                try:
                    loading_msg = await message.channel.send(embed=loading_embed)
                except discord.Forbidden:
                    # Last resort: send plain text
                    loading_msg = await message.channel.send("🔍 Шинэ мэдээ хайж байна...")
            
            articles = await self.news_service.fetch_latest_articles(4)  # Fetch 4 articles (2 from each source)
            
            if not articles:
                no_news_embed = discord.Embed(
                    title="📰 Мэдээ олдсонгүй",
                    description="Одоогоор шинэ мэдээ байхгүй байна. Дахин оролдоно уу.",
                    color=0xff6b6b
                )
                no_news_embed.set_footer(
                    text="🚀 GDG Ulaanbaatar",
                    icon_url="https://res.cloudinary.com/startup-grind/image/upload/c_fill,dpr_2.0,f_auto,g_center,h_1080,q_100,w_1080/v1/gcs/platform-data-goog/events/google-developers-group-gdg-icon_0.png"
                )
                try:
                    await loading_msg.edit(embed=no_news_embed)
                except (discord.Forbidden, discord.NotFound):
                    await message.channel.send("📰 Одоогоор шинэ мэдээ байхгүй байна.")
                return
            
            # Delete loading message and post articles
            try:
                await loading_msg.delete()
            except (discord.Forbidden, discord.NotFound):
                pass  # Ignore if we can't delete
            
            success_embed = discord.Embed(
                title="✅ Амжилттай",
                description=f"{len(articles)} шинэ мэдээ олдлоо!",
                color=0x51cf66
            )
            
            try:
                await message.reply(embed=success_embed, delete_after=3)
            except discord.Forbidden:
                try:
                    await message.channel.send(embed=success_embed, delete_after=3)
                except discord.Forbidden:
                    await message.channel.send(f"✅ {len(articles)} шинэ мэдээ олдлоо!")
            
            for article in articles:
                try:
                    embed = await self.create_news_embed(article)
                    await message.channel.send(embed=embed)
                    await asyncio.sleep(1)
                except discord.Forbidden:
                    # Fallback to plain text if embeds are not allowed
                    plain_text = f"**{article.title}**\n{article.description}\n🔗 {article.link}"
                    await message.channel.send(plain_text)
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Error posting article: {e}")
                    continue
                
        except Exception as e:
            logger.error(f"Error handling news request: {e}")
            try:
                error_embed = discord.Embed(
                    title="❌ Алдаа гарлаа",
                    description="Мэдээ татахад алдаа гарлаа. Дахин оролдоно уу.",
                    color=0xff6b6b
                )
                error_embed.set_footer(
                    text="🚀 GDG Ulaanbaatar",
                    icon_url="https://res.cloudinary.com/startup-grind/image/upload/c_fill,dpr_2.0,f_auto,g_center,h_1080,q_100,w_1080/v1/gcs/platform-data-goog/events/google-developers-group-gdg-icon_0.png"
                )
                await message.reply(embed=error_embed)
            except discord.Forbidden:
                try:
                    await message.channel.send("❌ Мэдээ татахад алдаа гарлаа. Дахин оролдоно уу.")
                except discord.Forbidden:
                    logger.error(f"Cannot send messages in channel {message.channel.id}")
                    pass
    
    async def handle_general_mention(self, message):
        """Handle general mentions"""
        try:
            responses = [
                {
                    "title": "👋 Сайн байна уу!",
                    "description": "Би GDG Ulaanbaatar-ын технологийн мэдээний бот байна.",
                    "color": 0x4285f4
                },
                {
                    "title": "🤖 Технологийн мэдээ",
                    "description": "Шинэ мэдээ авахыг хүсвэл **'шинэ мэдээ'** гэж бичээрэй.",
                    "color": 0x51cf66
                },
                {
                    "title": "ℹ️ Тусламж",
                    "description": "Дэлгэрэнгүй мэдээлэл авахыг хүсвэл **`!info`** командыг ашиглана уу.",
                    "color": 0x339af0
                }
            ]
            
            import random
            selected_response = random.choice(responses)
            
            # Check permissions
            if message.channel.permissions_for(message.guild.me).embed_links:
                embed = discord.Embed(
                    title=selected_response["title"],
                    description=selected_response["description"],
                    color=selected_response["color"]
                )
                
                embed.set_thumbnail(
                    url="https://res.cloudinary.com/startup-grind/image/upload/c_fill,dpr_2.0,f_auto,g_center,h_1080,q_100,w_1080/v1/gcs/platform-data-goog/events/google-developers-group-gdg-icon_0.png"
                )
                
                embed.set_footer(
                    text="🚀 GDG Ulaanbaatar • Mongolia",
                    icon_url="https://res.cloudinary.com/startup-grind/image/upload/c_fill,dpr_2.0,f_auto,g_center,h_1080,q_100,w_1080/v1/gcs/platform-data-goog/events/google-developers-group-gdg-icon_0.png"
                )
                
                try:
                    await message.reply(embed=embed)
                except discord.Forbidden:
                    await message.channel.send(embed=embed)
            else:
                # Fallback to plain text
                plain_text = f"{selected_response['title']}\n{selected_response['description']}"
                try:
                    await message.reply(plain_text)
                except discord.Forbidden:
                    await message.channel.send(plain_text)
                    
        except Exception as e:
            logger.error(f"Error handling general mention: {e}")
    
    def setup_commands(self):
        """Setup Discord bot commands"""
        
        @self.bot.command(name='news')
        async def fetch_news(ctx):
            """Manually fetch and post latest news"""
            if not ctx.author.guild_permissions.manage_messages:
                await ctx.send("Энэ командыг ашиглах эрх танд байхгүй байна.")
                return
            
            await ctx.send("Шинэ мэдээ татаж байна...")
            await self.fetch_and_post_news(force=True)
            await ctx.send("Мэдээ шинэчлэлт дууслаа.")
        
        @self.bot.command(name='status')
        async def bot_status(ctx):
            """Check bot status"""
            last_check = self.news_service.get_last_check_time()
            
            if last_check:
                # Convert UTC to Ulaanbaatar time for display
                if last_check.tzinfo is None:
                    last_check = last_check.replace(tzinfo=timezone.utc)
                last_check_ub = last_check.astimezone(ULAANBAATAR_TZ)
                last_check_str = last_check_ub.strftime("%Y-%m-%d %H:%M:%S (УБ)")
                
                # Calculate next scheduled time (UTC 01:00 daily)
                now_utc = datetime.now(timezone.utc)
                next_run_utc = now_utc.replace(hour=1, minute=0, second=0, microsecond=0)
                if now_utc.hour >= 1:  # If already past 1 AM today, schedule for tomorrow
                    next_run_utc += timedelta(days=1)
                next_run_ub = next_run_utc.astimezone(ULAANBAATAR_TZ)
                next_check_str = next_run_ub.strftime("%Y-%m-%d %H:%M:%S (УБ)")
            else:
                last_check_str = "Хэзээ ч"
                next_run_utc = datetime.now(timezone.utc).replace(hour=1, minute=0, second=0, microsecond=0)
                if datetime.now(timezone.utc).hour >= 1:
                    next_run_utc += timedelta(days=1)
                next_run_ub = next_run_utc.astimezone(ULAANBAATAR_TZ)
                next_check_str = next_run_ub.strftime("%Y-%m-%d %H:%M:%S (УБ)")
            
            embed = discord.Embed(
                title="🤖 GDG News Bot статус",
                description="Технологийн мэдээний ботын одоогийн байдал",
                color=0x4285f4,
                timestamp=datetime.now(ULAANBAATAR_TZ)
            )
            
            embed.add_field(
                name="⏰ Сүүлийн шалгалт", 
                value=f"```{last_check_str}```", 
                inline=True
            )
            embed.add_field(
                name="⏭️ Дараагийн шалгалт", 
                value=f"```{next_check_str}```", 
                inline=True
            )
            embed.add_field(
                name="🔄 Хуваарь", 
                value=f"```Өдөр бүр UTC 01:00```", 
                inline=True
            )
            embed.add_field(
                name="📺 Сувгууд", 
                value="\n".join([f"<#{cid}>" for cid in self.channel_ids]) if len(self.channel_ids) <= 5 else f"```{len(self.channel_ids)} суваг```",
                inline=True
            )
            embed.add_field(
                name="📊 Серверүүд", 
                value=f"```{len(ctx.bot.guilds)} сервер```", 
                inline=True
            )
            embed.add_field(
                name="🌐 Эх сурвалж", 
                value="```The Verge + CNET```", 
                inline=True
            )
            embed.add_field(
                name="🔍 Tech Filter", 
                value=f"```{'Enabled' if self.strict_tech_filter else 'Disabled'}```", 
                inline=True
            )
            
            embed.set_thumbnail(
                url="https://res.cloudinary.com/startup-grind/image/upload/c_fill,dpr_2.0,f_auto,g_center,h_1080,q_100,w_1080/v1/gcs/platform-data-goog/events/google-developers-group-gdg-icon_0.png"
            )
            
            embed.set_footer(
                text="🚀 GDG Ulaanbaatar • Mongolia",
                icon_url="https://res.cloudinary.com/startup-grind/image/upload/c_fill,dpr_2.0,f_auto,g_center,h_1080,q_100,w_1080/v1/gcs/platform-data-goog/events/google-developers-group-gdg-icon_0.png"
            )
            
            await ctx.send(embed=embed)
        
        @self.bot.command(name='info')
        async def info_command(ctx):
            """Show bot information and help"""
            embed = discord.Embed(
                title="ℹ️ GDG Ulaanbaatar News Bot тусламж",
                description="🤖 Технологийн мэдээний бот • The Verge-ээс мэдээ авч орчуулдаг",
                color=0x4285f4
            )
            
            embed.add_field(
                name="⚡ Командууд",
                value="""
                🔍 `!news` - Шинэ мэдээ татах (админ)
                📊 `!status` - Ботын статус шалгах  
                ℹ️ `!info` - Энэ тусламжийг харах
                🔐 `!checkperms` - Зөвшөөрөл шалгах
                """,
                inline=False
            )
            
            embed.add_field(
                name="💬 Ментион",
                value="```@GDG UB BOT шинэ мэдээ юу байна?```\nШинэ мэдээ харахын тулд ботыг дуудаарай",
                inline=False
            )
            
            embed.add_field(
                name="🔄 Автомат мэдээ",
                value=f"```Өдөр бүр UTC 01:00```\nАвтоматаар өдөр бүр шинэ мэдээ шалгаж пост хийдэг",
                inline=False
            )
            
            embed.add_field(
                name="🌍 Орчуулга",
                value="```Англи ➜ Монгол```\nThe Verge болон CNET-ээс авсан мэдээг монгол хэл рүү орчуулна",
                inline=True
            )
            
            embed.add_field(
                name="📰 Эх сурвалж",
                value="```The Verge + CNET```\nДэлхийн шилдэг технологийн мэдээний сайтууд",
                inline=True
            )
            
            embed.add_field(
                name="🏢 Байгууллага",
                value="```GDG Ulaanbaatar```\nGoogle Developers Group Mongolia",
                inline=True
            )
            
            embed.set_thumbnail(
                url="https://res.cloudinary.com/startup-grind/image/upload/c_fill,dpr_2.0,f_auto,g_center,h_1080,q_100,w_1080/v1/gcs/platform-data-goog/events/google-developers-group-gdg-icon_0.png"
            )
            
            embed.set_footer(
                text="🚀 GDG Ulaanbaatar • Made with ❤️ in Mongolia",
                icon_url="https://res.cloudinary.com/startup-grind/image/upload/c_fill,dpr_2.0,f_auto,g_center,h_1080,q_100,w_1080/v1/gcs/platform-data-goog/events/google-developers-group-gdg-icon_0.png"
            )
            
            await ctx.send(embed=embed)
        
        @self.bot.command(name='checkperms', aliases=['permissions', 'зөвшөөрөл'])
        async def check_permissions(ctx):
            """Check bot permissions in current channel"""
            if not ctx.guild:
                await ctx.send("❌ Энэ команд зөвхөн серверт ажиллана.")
                return
                
            channel = ctx.channel
            bot_member = ctx.guild.get_member(self.bot.user.id)
            
            if not bot_member:
                await ctx.send("❌ Бот гишүүний мэдээлэл олдсонгүй.")
                return
                
            perms = channel.permissions_for(bot_member)
            
            # Check essential permissions
            essential_perms = {
                'send_messages': 'Мессеж илгээх',
                'embed_links': 'Embed линк хийх', 
                'attach_files': 'Файл хавсаргах',
                'read_message_history': 'Мессежийн түүх унших',
                'add_reactions': 'Reaction нэмэх',
                'mention_everyone': 'Бүгдийг дуудах'
            }
            
            embed = discord.Embed(
                title="🔐 Зөвшөөрлийн шалгалт",
                description=f"📺 {channel.mention} каналын зөвшөөрлүүд:",
                color=0x4285f4
            )
            
            permissions_text = ""
            all_good = True
            
            for perm_name, perm_desc in essential_perms.items():
                has_perm = getattr(perms, perm_name, False)
                status = "✅" if has_perm else "❌"
                permissions_text += f"{status} {perm_desc}\n"
                if not has_perm:
                    all_good = False
            
            embed.add_field(
                name="📋 Зөвшөөрлүүд",
                value=permissions_text,
                inline=False
            )
            
            # Overall status
            if all_good:
                embed.add_field(
                    name="✅ Нийт төлөв",
                    value="Бүх зөвшөөрөл байна! Бот хэвийн ажиллана.",
                    inline=False
                )
                embed.color = 0x00FF00  # Green
            else:
                embed.add_field(
                    name="⚠️ Нийт төлөв", 
                    value="Зарим зөвшөөрөл дутуу байна. Админтайгаа холбогдоно уу.",
                    inline=False
                )
                embed.color = 0xFF9900  # Orange
            
            embed.set_footer(text="💡 Админ: Ботыг канал тохиргоонд нэмж зөвшөөрөл өгнө үү")
            
            try:
                await ctx.send(embed=embed)
            except discord.Forbidden:
                # Fallback text if embed permissions are missing
                fallback_text = f"🔐 Зөвшөөрлийн шалгалт - {channel.mention}\n\n"
                for perm_name, perm_desc in essential_perms.items():
                    has_perm = getattr(perms, perm_name, False)
                    status = "✅" if has_perm else "❌"
                    fallback_text += f"{status} {perm_desc}\n"
                
                if all_good:
                    fallback_text += "\n✅ Бүх зөвшөөрөл байна!"
                else:
                    fallback_text += "\n⚠️ Зарим зөвшөөрөл дутуу байна."
                    
                await ctx.send(fallback_text)

    @tasks.loop(minutes=60)  # Check every hour to catch the scheduled time
    async def news_check_task(self):
        """Background task to check for new news at UTC 01:00 daily"""
        try:
            current_utc = datetime.now(timezone.utc)
            
            # Check if it's the scheduled time (UTC 01:00)
            if current_utc.hour == self.scheduled_hour and current_utc.minute < 60:
                last_check = self.news_service.get_last_check_time()
                
                # Ensure we don't post multiple times within the same hour
                if last_check:
                    time_since_last = current_utc - last_check.replace(tzinfo=timezone.utc) if last_check.tzinfo is None else current_utc - last_check
                    if time_since_last.total_seconds() < 3600:  # Less than 1 hour ago
                        logger.debug("Already posted news within the last hour, skipping...")
                        return
                
                logger.info(f"Scheduled news check at UTC {current_utc.strftime('%H:%M')} - fetching tech news...")
                await self.fetch_and_post_news()
        
        except Exception as e:
            logger.error(f"Error in scheduled news checking task: {e}")
    
    async def create_news_embed(self, article: NewsArticle) -> discord.Embed:
        """Create a Discord embed for a news article"""
        try:
            translated_title = await self.translation_service.translate_to_mongolian(article.title)
            translated_description = await self.translation_service.translate_to_mongolian(article.description)
            
            embed = discord.Embed(
                title=translated_title,
                description=translated_description,
                url=article.link,
                color=0x4285f4,
                timestamp=article.published
            )
            
            # Add original title field with better formatting
            embed.add_field(
                name="📰 Анхны гарчиг",
                value=f"```{article.title}```",
                inline=False
            )
            
            # Add news source info
            embed.add_field(
                name="📅 Огноо",
                value=article.published.strftime("%Y-%m-%d %H:%M"),
                inline=True
            )
            
            embed.add_field(
                name="✍️ Эх сурвалж",
                value=article.author,
                inline=True
            )
            
            embed.add_field(
                name="🔗 Линк",
                value=f"[{article.author}]({article.link})",
                inline=True
            )
            
            # Set author with appropriate branding based on source
            if "verge" in article.author.lower():
                embed.set_author(
                    name="The Verge • Tech News",
                    icon_url="https://cdn.vox-cdn.com/uploads/chorus_asset/file/7395359/favicon-16x16.0.png",
                    url="https://www.theverge.com"
                )
                # Add The Verge logo as thumbnail
                embed.set_thumbnail(
                    url="https://cdn.vox-cdn.com/uploads/chorus_asset/file/13668586/the_verge_logo.0.png"
                )
            else:  # CNET
                embed.set_author(
                    name="CNET • Tech News",
                    icon_url="https://www.cnet.com/favicon.ico",
                    url="https://www.cnet.com"
                )
                # Add CNET logo as thumbnail
                embed.set_thumbnail(
                    url="https://www.cnet.com/a/img/resize/c5a6b06db66b5c7be5d46f2d83bbe2ad79a8a8ba/hub/2019/04/15/b6ad96c7-34e0-45fa-bc76-6dd37b2c6db8/cnet-logo-og-1200x630.jpg?auto=webp&fit=crop&height=675&width=1200"
                )
            
            # Enhanced footer with GDG branding
            embed.set_footer(
                text="🚀 Технологийн мэдээ • GDG Ulaanbaatar • Mongolia",
                icon_url="https://res.cloudinary.com/startup-grind/image/upload/c_fill,dpr_2.0,f_auto,g_center,h_1080,q_100,w_1080/v1/gcs/platform-data-goog/events/google-developers-group-gdg-icon_0.png"
            )
            
            return embed
            
        except Exception as e:
            logger.error(f"Error creating embed: {e}")
            # Fallback to original content with basic formatting
            embed = discord.Embed(
                title=article.title,
                description=article.description,
                url=article.link,
                color=0x4285f4,
                timestamp=article.published
            )
            
            embed.set_author(
                name=article.author,
                icon_url="https://cdn.vox-cdn.com/uploads/chorus_asset/file/7395359/favicon-16x16.0.png" if "verge" in article.author.lower() else "https://www.cnet.com/favicon.ico"
            )
            
            embed.set_footer(
                text="Tech News • GDG Ulaanbaatar",
                icon_url="https://res.cloudinary.com/startup-grind/image/upload/c_fill,dpr_2.0,f_auto,g_center,h_1080,q_100,w_1080/v1/gcs/platform-data-goog/events/google-developers-group-gdg-icon_0.png"
            )
            
            return embed
    
    async def fetch_and_post_news(self, force: bool = False):
        """Fetch news and post to Discord channels"""
        try:
            articles = await self.news_service.fetch_latest_articles(self.max_news_per_post)
            
            if not articles:
                if force:
                    logger.info("No recent tech news found")
                return
            
            if not self.channel_ids:
                logger.error("No Discord channels configured!")
                return
            
            # Post to all configured channels
            successful_posts = 0
            for channel_id in self.channel_ids:
                try:
                    channel = self.bot.get_channel(channel_id)
                    if not channel:
                        logger.error(f"Could not find Discord channel with ID: {channel_id}")
                        continue
                    
                    # Check permissions
                    permissions = channel.permissions_for(channel.guild.me)
                    if not permissions.send_messages:
                        logger.error(f"No permission to send messages in channel #{channel.name} ({channel_id})")
                        continue
                    
                    for i, article in enumerate(articles):
                        try:
                            if permissions.embed_links:
                                embed = await self.create_news_embed(article)
                                await channel.send(embed=embed)
                            else:
                                # Fallback to plain text
                                plain_text = f"**{article.title}**\n{article.description}\n🔗 {article.link}\n📅 {article.published.strftime('%Y-%m-%d %H:%M')}"
                                await channel.send(plain_text)
                            
                            if i < len(articles) - 1:
                                await asyncio.sleep(1)  # Shorter delay between articles
                                
                        except discord.Forbidden as e:
                            logger.error(f"Permission error posting to channel {channel_id}: {e}")
                            break  # Skip remaining articles for this channel
                        except Exception as e:
                            logger.error(f"Error posting article to channel {channel_id}: {e}")
                            continue
                    
                    successful_posts += 1
                    logger.info(f"Posted {len(articles)} articles to channel #{channel.name} ({channel_id})")
                    
                    # Delay between different channels to avoid rate limits
                    if len(self.channel_ids) > 1:
                        await asyncio.sleep(3)
                        
                except Exception as e:
                    logger.error(f"Error posting to channel {channel_id}: {e}")
                    continue
            
            if successful_posts > 0:
                self.news_service.save_last_check_time()
                logger.info(f"Successfully posted to {successful_posts}/{len(self.channel_ids)} channels")
            
        except Exception as e:
            logger.error(f"Error in fetch_and_post_news: {e}")
    
    def run(self):
        """Start the Discord bot"""
        if not self.token:
            logger.error("DISCORD_TOKEN not found in environment variables!")
            return
        
        if not self.channel_ids:
            logger.error("No Discord channels configured! Please set DISCORD_CHANNEL_IDS or DISCORD_CHANNEL_ID in .env file!")
            return
        
        logger.info("Starting GDG News Bot...")
        logger.info(f"Configured channels: {len(self.channel_ids)}")
        logger.info(f"Scheduled time: Daily at UTC {self.scheduled_hour:02d}:00")
        logger.info(f"News sources: The Verge + CNET (4 articles total)")
        logger.info(f"Tech filter: {'Enabled' if self.strict_tech_filter else 'Disabled'}")
        self.bot.run(self.token)

def main():
    bot = GDGNewsBot()
    bot.run()

if __name__ == "__main__":
    main()