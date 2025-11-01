#!/usr/bin/env python3
"""
Scrape fresh news content from all configured sources
Used by GitHub Actions workflow before podcast generation
"""

import asyncio
import sys
import os
import json
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def main():
    """Scrape all news sources and save to scraped_content.json"""
    try:
        from scraper import NewsScraper
        
        logger.info("📰 Starting news scraping...")
        scraper = NewsScraper(sources_file='sources.json')
        data = await scraper.scrape_all()
        
        # Save scraped data
        with open('scraped_content.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Successfully scraped {len(data)} sources")
        logger.info(f"📁 Saved to scraped_content.json")
        
        return 0
    except Exception as e:
        logger.error(f"❌ Scraping failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
