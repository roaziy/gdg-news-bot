import discord
from discord.ext import commands, tasks
import feedparser
import asyncio
import os
from datetime import datetime, timedelta
import json
from googletrans import Translator
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
        self.translator = Translator()
        self.max_chunk_size = 500
    
    async def translate_to_mongolian(self, text: str) -> str:
        """Translate text to Mongolian with chunking for long texts"""
        try:
            if len(text) <= self.max_chunk_size:
                result = self.translator.translate(text, dest='mn')
                return result.text
            
            # Split text into sentences and translate in chunks
            sentences = text.split('. ')
            translated_chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk + sentence) < self.max_chunk_size:
                    current_chunk += sentence + ". "
                else:
                    if current_chunk:
                        result = self.translator.translate(current_chunk.strip(), dest='mn')
                        translated_chunks.append(result.text)
                        current_chunk = sentence + ". "
                    else:
                        result = self.translator.translate(sentence, dest='mn')
                        translated_chunks.append(result.text)
            
            if current_chunk:
                result = self.translator.translate(current_chunk.strip(), dest='mn')
                translated_chunks.append(result.text)
            
            return " ".join(translated_chunks)
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return f"[Орчуулга амжилтгүй] {text}"

class NewsService:
    """Handles fetching and processing news from The Verge"""
    
    def __init__(self):
        self.rss_url = "https://www.theverge.com/rss/index.xml"
        self.last_check_file = 'last_check.json'
    
    def clean_html(self, html_text: str) -> str:
        """Remove HTML tags from text"""
        try:
            soup = BeautifulSoup(html_text, 'html.parser')
            text = soup.get_text()
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        except Exception:
            return html_text
    
    async def fetch_latest_articles(self, max_articles: int = 3) -> List[NewsArticle]:
        """Fetch latest tech news articles from The Verge"""
        try:
            feed = feedparser.parse(self.rss_url)
            
            if not feed.entries:
                logger.warning("No entries found in The Verge RSS feed")
                return []
            
            articles = []
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            for entry in feed.entries[:10]:
                try:
                    pub_date = datetime(*entry.published_parsed[:6])
                    
                    if pub_date > cutoff_time:
                        description = self.clean_html(entry.description)
                        if len(description) > 300:
                            description = description[:300] + "..."
                        
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
        self.channel_id = int(os.getenv('DISCORD_CHANNEL_ID', 0))
        self.check_interval = int(os.getenv('NEWS_CHECK_INTERVAL_HOURS', 4))
        self.max_news_per_post = int(os.getenv('MAX_NEWS_PER_POST', 3))
        
        # Services
        self.news_service = NewsService()
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
            # Create loading embed
            loading_embed = discord.Embed(
                title="🔍 Шинэ мэдээ хайж байна...",
                description="The Verge-ээс хамгийн сүүлийн технологийн мэдээг авч байна",
                color=0xffa500
            )
            loading_embed.set_thumbnail(
                url="https://cdn.vox-cdn.com/uploads/chorus_asset/file/13668586/the_verge_logo.0.png"
            )
            
            loading_msg = await message.reply(embed=loading_embed)
            
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
                await loading_msg.edit(embed=no_news_embed)
                return
            
            # Delete loading message and post articles
            await loading_msg.delete()
            
            success_embed = discord.Embed(
                title="✅ Амжилттай",
                description=f"{len(articles)} шинэ мэдээ олдлоо!",
                color=0x51cf66
            )
            await message.reply(embed=success_embed, delete_after=3)
            
            for article in articles:
                embed = await self.create_news_embed(article)
                await message.channel.send(embed=embed)
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error handling news request: {e}")
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
    
    async def handle_general_mention(self, message):
        """Handle general mentions"""
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
        
        await message.reply(embed=embed)
    
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
                name="📺 Суваг", 
                value=f"<#{self.channel_id}>", 
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
        """Fetch news and post to Discord channel"""
        try:
            articles = await self.news_service.fetch_latest_articles(self.max_news_per_post)
            
            if not articles:
                if force:
                    logger.info("No recent news found")
                return
            
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                logger.error(f"Could not find Discord channel with ID: {self.channel_id}")
                return
            
            for i, article in enumerate(articles):
                try:
                    embed = await self.create_news_embed(article)
                    await channel.send(embed=embed)
                    
                    if i < len(articles) - 1:
                        await asyncio.sleep(2)
                        
                except Exception as e:
                    logger.error(f"Error posting article: {e}")
                    continue
            
            self.news_service.save_last_check_time()
            logger.info(f"Posted {len(articles)} news articles to Discord")
            
        except Exception as e:
            logger.error(f"Error in fetch_and_post_news: {e}")
    
    def run(self):
        """Start the Discord bot"""
        if not self.token:
            logger.error("DISCORD_TOKEN not found in environment variables!")
            return
        
        if not self.channel_id:
            logger.error("DISCORD_CHANNEL_ID not found in environment variables!")
            return
        
        logger.info("Starting GDG News Bot...")
        self.bot.run(self.token)

def main():
    bot = GDGNewsBot()
    bot.run()

if __name__ == "__main__":
    main()
