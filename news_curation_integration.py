#!/usr/bin/env python3
"""
NEWS CURATION INTEGRATION
Integrerar multi-agent systemet i run_podcast_complete.py
"""

import json
import logging
from typing import List, Dict
from news_agent_system import NewsOrchestrator, NewsArticle
import asyncio

logger = logging.getLogger(__name__)


async def curate_news_with_agents(scraped_content_path: str = 'scraped_content.json') -> List[Dict]:
    """
    Använd agent-systemet för att kurera nyheter
    Returnerar lista av valda artiklar i format kompatibelt med run_podcast_complete.py
    """
    
    # Läs in scrapade artiklar
    with open(scraped_content_path, 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)
    
    # Konvertera till flat lista av artiklar
    raw_articles = []
    for source_group in scraped_data:
        source_name = source_group.get('source', 'Okänd')
        items = source_group.get('items', [])
        
        for item in items:
            raw_articles.append({
                'source': source_name,
                'title': item.get('title', ''),
                'content': item.get('content', ''),
                'link': item.get('link', '')
            })
    
    logger.info(f"[AGENT-CURATION] Bearbetar {len(raw_articles)} artiklar från {len(scraped_data)} källor")
    
    # Kör genom agent-systemet
    orchestrator = NewsOrchestrator()
    selected_articles = await orchestrator.process_articles(raw_articles)
    
    # Konvertera tillbaka till format som run_podcast_complete förväntar sig
    result = []
    for article in selected_articles:
        result.append({
            'source': article.source,
            'title': article.title,
            'content': article.content,
            'link': article.link,
            'category': article.category.value if article.category else 'unknown',
            'relevance_score': article.relevance_score,
            'geographic_region': article.geographic_region
        })
    
    logger.info(f"[AGENT-CURATION] ✅ Valde {len(result)} artiklar för podcast")
    
    return result


def curate_news_sync(scraped_content_path: str = 'scraped_content.json') -> List[Dict]:
    """Synkron wrapper för async curate_news_with_agents"""
    return asyncio.run(curate_news_with_agents(scraped_content_path))


if __name__ == "__main__":
    # Test
    articles = curate_news_sync()
    print(f"\n✅ Kuraterade {len(articles)} artiklar:")
    for i, article in enumerate(articles, 1):
        print(f"{i}. [{article['category']}] {article['title'][:60]}...")
        print(f"   Relevans: {article['relevance_score']}/100")
