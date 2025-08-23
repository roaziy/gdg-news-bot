#!/usr/bin/env python3
"""
Test the enhanced tech filtering to see what articles pass
"""

import feedparser
import requests
from datetime import datetime, timedelta

# Copy the enhanced filtering function
def is_tech_news(title: str, description: str, categories: list = None) -> bool:
    """Enhanced filter to check if article is actually tech-related using RSS categories"""
    
    # Priority 1: Check RSS categories first (most reliable)
    if categories:
        category_names = [cat.lower() for cat in categories]
        
        # Strict exclusion categories - if article has these, it's NOT tech
        strict_exclude_categories = [
            'politics', 'policy', 'entertainment', 'film', 'tv shows', 'streaming',
            'sports', 'health', 'medical', 'climate', 'environment', 'culture', 
            'food', 'travel', 'lifestyle', 'speech', 'command line'
        ]
        
        # Check for strict exclusions first
        for exclude_cat in strict_exclude_categories:
            if any(exclude_cat in cat for cat in category_names):
                # Only allow if it's PURELY tech-focused (has core tech categories)
                core_tech_in_cats = any(cat in category_names for cat in ['tech', 'ai', 'apple', 'google', 'microsoft', 'meta', 'intel', 'nvidia', 'hardware', 'software'])
                if not core_tech_in_cats:
                    return False
                # Even with tech categories, exclude political/policy articles
                if any(pol_cat in category_names for pol_cat in ['politics', 'policy']):
                    return False
        
        # Core tech categories that indicate tech content
        pure_tech_categories = [
            'tech', 'ai', 'apple', 'google', 'microsoft', 'meta', 'amazon',
            'intel', 'nvidia', 'amd', 'samsung', 'hardware', 'software',
            'gadgets', 'mobile', 'computing', 'cybersecurity', 'blockchain',
            'cryptocurrency', 'robotics', 'automation', 'innovation'
        ]
        
        # Include if article has pure tech categories
        for tech_cat in pure_tech_categories:
            if any(tech_cat in cat for cat in category_names):
                return True
        
        # Gaming is tech, but only if it's about gaming technology/industry
        if 'gaming' in category_names:
            # Allow gaming if it doesn't have pure entertainment categories
            if not any(ent_cat in category_names for ent_cat in ['entertainment', 'games review']):
                return True
    
    # Priority 2: Fallback to keyword analysis for articles without categories
    content = f"{title} {description}".lower()
    
    # Strong exclusion keywords for non-tech content
    exclude_keywords = [
        'politics', 'election', 'congress', 'senate', 'president', 'government policy',
        'climate change', 'global warming', 'environment', 'health crisis',
        'movie', 'film', 'tv show', 'celebrity', 'entertainment industry',
        'sports', 'football', 'basketball', 'olympics'
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
        'software', 'app store', 'operating system', 'cloud computing', 'api',
        'programming', 'coding', 'developer'
    ]
    
    # Check for core tech keywords
    tech_score = 0
    for keyword in core_tech_keywords:
        if keyword in content:
            tech_score += 1
    
    # Require at least 1 strong tech keyword match
    return tech_score > 0

def clean_html(html_text: str) -> str:
    """Remove HTML tags from text"""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_text, 'html.parser')
        return soup.get_text()
    except:
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', html_text)

def main():
    print("🔍 TESTING ENHANCED TECH FILTERING")
    print("=" * 50)
    
    # Use proper headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get('https://www.theverge.com/rss/index.xml', headers=headers, timeout=10)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            print(f"📰 Found {len(feed.entries)} total articles")
            print()
            
            tech_articles = []
            non_tech_articles = []
            
            for entry in feed.entries:
                # Get categories
                categories = []
                if hasattr(entry, 'tags'):
                    categories = [tag.term for tag in entry.tags]
                
                # Clean description
                description = clean_html(entry.description)
                if len(description) > 200:
                    description = description[:200] + "..."
                
                # Test filtering
                is_tech = is_tech_news(entry.title, description, categories)
                
                if is_tech:
                    tech_articles.append((entry.title, categories))
                else:
                    non_tech_articles.append((entry.title, categories))
            
            print(f"✅ TECH ARTICLES ({len(tech_articles)}):")
            print("-" * 30)
            for i, (title, cats) in enumerate(tech_articles, 1):
                print(f"{i}. {title}")
                print(f"   Categories: {cats}")
                print()
            
            print(f"❌ NON-TECH ARTICLES ({len(non_tech_articles)}):")
            print("-" * 30)
            for i, (title, cats) in enumerate(non_tech_articles, 1):
                print(f"{i}. {title}")
                print(f"   Categories: {cats}")
                print()
            
            print("📊 SUMMARY:")
            print(f"Total articles: {len(feed.entries)}")
            print(f"Tech articles: {len(tech_articles)}")
            print(f"Non-tech articles: {len(non_tech_articles)}")
            print(f"Tech filter success rate: {len(tech_articles)/len(feed.entries)*100:.1f}%")
            
        else:
            print(f"❌ Failed to fetch RSS feed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
