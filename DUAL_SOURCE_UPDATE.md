# GDG News Bot - Dual Source Update

## Changes Made

### 📅 Scheduling Changes

- **Old**: Every 4-5 hours interval checking
- **New**: Daily at **UTC 01:00** (9:00 AM Ulaanbaatar time)
- **Benefits**: More predictable, consistent daily news updates

### 📰 News Sources

- **Old**: Only The Verge (3 articles)
- **New**: The Verge + CNET (2 articles each = 4 total)
- **RSS Feeds**:
  - The Verge: `https://www.theverge.com/rss/index.xml`
  - CNET: `https://www.cnet.com/rss/news/`

### 🔧 Technical Improvements

#### NewsService Class

- Added dual-source fetching with `_fetch_from_source()` method
- Enhanced filtering with 36-hour cutoff for daily checks
- Source-specific article attribution
- Improved error handling per source

#### Scheduling System

- Changed from interval-based (`@tasks.loop(hours=4)`) to time-based (`@tasks.loop(minutes=60)`)
- Added UTC 01:00 daily trigger logic
- Prevents duplicate posts within the same hour
- Better timezone handling

#### Discord Embeds

- Dynamic source branding (The Verge vs CNET logos)
- Source-specific icons and thumbnails
- Updated embed descriptions and footers
- Improved fallback handling

### 🎯 User Experience

- **Status Command**: Shows next scheduled time in UB timezone
- **Manual Requests**: Now fetch 4 articles from both sources
- **Loading Messages**: Updated to mention both sources
- **Error Handling**: More robust for multiple RSS sources

### 🕐 Time Display

- **Bot displays**: All times in Ulaanbaatar timezone (UTC+8)
- **Internal logic**: Uses UTC for scheduling consistency
- **Next run calculation**: Shows accurate daily schedule

## Testing Results

✅ **RSS Feeds**: Both The Verge and CNET feeds working  
✅ **Dual Fetching**: Successfully gets 2 articles from each source  
✅ **Tech Filtering**: Enhanced filtering works with both sources  
✅ **Scheduling**: UTC 01:00 daily trigger logic verified  
✅ **Bot Initialization**: All imports and configurations working

## Deployment Notes

- No new dependencies required
- Existing `.env` configuration remains compatible
- Bot will automatically start using new schedule after restart
- Current channel permissions remain unchanged

## Next Steps

1. **Deploy to Render.com**: Push changes and restart service
2. **Monitor First Run**: Verify UTC 01:00 trigger works
3. **Test Dual Sources**: Confirm both news sources appear in posts
4. **User Communication**: Inform server admins about new schedule

---

**Daily Schedule**: UTC 01:00 → UB 09:00 AM  
**Articles**: 4 total (2 Verge + 2 CNET)  
**Tech Filter**: Enhanced for both sources  
**Translation**: Mongolian translation preserved
