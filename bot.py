import discord
from discord.ext import commands, tasks
import feedparser
import asyncio
import os
from datetime import datetime, timedelta
import json
from deep_translator import GoogleTranslator
from dotenv import load_dotenv
import logging
import aiohttp
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional

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
    """Handles fetching and processing news from The Verge"""
    
    def __init__(self):
        # Use The Verge's main RSS feed and filter by tech categories
        self.rss_url = "https://www.theverge.com/rss/index.xml"
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

    async def fetch_latest_articles(self, max_articles: int = 3) -> List[NewsArticle]:
        """Fetch latest tech news articles from The Verge"""
        try:
            feed = feedparser.parse(self.rss_url)
            
            if not feed.entries:
                logger.warning("No entries found in The Verge RSS feed")
                return []
            
            articles = []
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            for entry in feed.entries[:20]:  # Check more articles to find tech ones
                try:
                    pub_date = datetime(*entry.published_parsed[:6])
                    
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
                                author=getattr(entry, 'author', 'The Verge')
                            )
                            articles.append(article)
                        
                except Exception as e:
                    logger.error(f"Error processing article: {e}")
                    continue
            
            # Sort by publication date (newest first)
            articles.sort(key=lambda x: x.published, reverse=True)
            return articles[:max_articles]
            
        except Exception as e:
            logger.error(f"Error fetching news from The Verge: {e}")
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
                json.dump({'last_check': datetime.utcnow().isoformat()}, f)
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
        
        self.check_interval = int(os.getenv('NEWS_CHECK_INTERVAL_HOURS', 4))
        self.max_news_per_post = int(os.getenv('MAX_NEWS_PER_POST', 3))
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
                content = message.content.lower()
                
                # Mongolian greetings and news requests
                mongolian_keywords = [
                    'шинэ мэдээ', 'мэдээ', 'юу байна', 'сонин', 
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
                description="The Verge-ээс хамгийн сүүлийн технологийн мэдээг авч байна",
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
            
            articles = await self.news_service.fetch_latest_articles(2)
            
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
                last_check_str = last_check.strftime("%Y-%m-%d %H:%M:%S UTC")
                next_check = last_check + timedelta(hours=self.check_interval)
                next_check_str = next_check.strftime("%Y-%m-%d %H:%M:%S UTC")
            else:
                last_check_str = "Хэзээ ч"
                next_check_str = "Удахгүй"
            
            embed = discord.Embed(
                title="🤖 GDG News Bot статус",
                description="Технологийн мэдээний ботын одоогийн байдал",
                color=0x4285f4,
                timestamp=datetime.utcnow()
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
                name="🔄 Шалгах интервал", 
                value=f"```{self.check_interval} цаг```", 
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
                value="```The Verge RSS```", 
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
                value=f"```{self.check_interval} цаг тутам```\nАвтоматаар шинэ мэдээ шалгаж пост хийдэг",
                inline=False
            )
            
            embed.add_field(
                name="🌍 Орчуулга",
                value="```Англи ➜ Монгол```\nThe Verge-ээс авсан мэдээг монгол хэл рүү орчуулна",
                inline=True
            )
            
            embed.add_field(
                name="📰 Эх сурвалж",
                value="```The Verge```\nДэлхийн шилдэг технологийн мэдээний сайт",
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

    @tasks.loop(hours=1)
    async def news_check_task(self):
        """Background task to check for new news"""
        try:
            last_check = self.news_service.get_last_check_time()
            current_time = datetime.utcnow()
            
            if not last_check or (current_time - last_check).total_seconds() >= self.check_interval * 3600:
                logger.info("Checking for new tech news...")
                await self.fetch_and_post_news()
        
        except Exception as e:
            logger.error(f"Error in news checking task: {e}")
    
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
                name="✍️ Зохиогч",
                value=article.author,
                inline=True
            )
            
            embed.add_field(
                name="🔗 Эх сурвалж",
                value="[The Verge](https://www.theverge.com)",
                inline=True
            )
            
            # Set author with The Verge branding
            embed.set_author(
                name="The Verge • Tech News",
                icon_url="https://cdn.vox-cdn.com/uploads/chorus_asset/file/7395359/favicon-16x16.0.png",
                url="https://www.theverge.com"
            )
            
            # Add The Verge logo as thumbnail
            embed.set_thumbnail(
                url="https://cdn.vox-cdn.com/uploads/chorus_asset/file/13668586/the_verge_logo.0.png"
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
                name="The Verge",
                icon_url="https://cdn.vox-cdn.com/uploads/chorus_asset/file/7395359/favicon-16x16.0.png"
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
        logger.info(f"Tech filter: {'Enabled' if self.strict_tech_filter else 'Disabled'}")
        self.bot.run(self.token)

def main():
    bot = GDGNewsBot()
    bot.run()

if __name__ == "__main__":
    main()
