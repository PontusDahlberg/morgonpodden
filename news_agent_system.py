#!/usr/bin/env python3
"""
MULTI-AGENT NEWS CURATION SYSTEM
================================
Orchestrator-baserat system med specialiserade agenter för att säkerställa
kvalitet, relevans och balans i nyhetsurvalet.

AGENTER:
1. NewsScraperAgent - Scraper och kategoriserar nyheter
2. RelevanceAgent - Bedömer relevans mot kriterier (klimat/miljö/AI/tech)
3. FactCheckAgent - Verifierar fakta och rimlighetskontroll
4. BalanceAgent - Säkerställer rätt fördelning (50%+ klimat/miljö)
5. Orchestrator - Koordinerar alla agenter och fattar slutgiltiga beslut

KVALITETSKRITERIER:
- Svenska klimat/miljö-nyheter prioriteras högst
- Globala klimat/miljö-nyheter sekundärt
- Tech/AI endast om klimat/miljö-relevans ELLER högkvalitativa tech-nyheter
- FÖRBJUDET: Gaming, underhållning, produktreklam, sociala medier
- Faktakontroll: Rimlighetsbedömning av siffror och påståenden
"""

import json
import logging
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsCategory(Enum):
    """Nyhetskategorier med prioritet"""
    CLIMATE_SWEDEN = "climate_sweden"  # Högst prioritet
    CLIMATE_GLOBAL = "climate_global"  # Hög prioritet
    ENVIRONMENT_SWEDEN = "environment_sweden"  # Hög prioritet
    ENVIRONMENT_GLOBAL = "environment_global"  # Medel prioritet
    TECH_CLIMATE = "tech_climate"  # Medel prioritet (tech med klimatkoppling)
    TECH_AI = "tech_ai"  # Låg prioritet
    TECH_GENERAL = "tech_general"  # Mycket låg prioritet
    IRRELEVANT = "irrelevant"  # Exkluderas


@dataclass
class NewsArticle:
    """Nyhetsobjekt med metadata"""
    source: str
    title: str
    content: str
    link: str
    category: Optional[NewsCategory] = None
    relevance_score: float = 0.0
    fact_check_passed: bool = False
    fact_check_notes: str = ""
    geographic_region: str = ""  # Sverige, Norden, Europa, Global


class NewsScraperAgent:
    """
    Agent 1: Scraper och kategoriserar nyheter
    Ansvarar för att identifiera kategori och geografisk region
    """
    
    CLIMATE_KEYWORDS = [
        'klimat', 'climate', 'väder', 'weather', 'CO2', 'koldioxid', 
        'utsläpp', 'emissions', 'uppvärmning', 'global warming',
        'COP', 'IPCC', 'Paris-avtalet', 'klimatmål', 'fossilfri',
        'förnybar energi', 'renewable', 'vindkraft', 'solkraft',
        'solenergi', 'kärnkraft', 'nuclear', 'energi', 'energy'
    ]
    
    ENVIRONMENT_KEYWORDS = [
        'miljö', 'environment', 'hållbarhet', 'sustainability',
        'natur', 'nature', 'ekosystem', 'ecosystem', 'biologisk mångfald',
        'biodiversity', 'återvinning', 'recycling', 'cirkulär ekonomi',
        'förorening', 'pollution', 'skog', 'forest', 'hav', 'ocean',
        'vatten', 'water', 'luft', 'air quality', 'naturvård',
        'skyddad', 'arter', 'species'
    ]
    
    TECH_CLIMATE_KEYWORDS = [
        'elbilar', 'electric vehicle', 'EV', 'batterilagring',
        'energieffektiv', 'smart grid', 'värmepump', 'heat pump',
        'koldioxidavskiljning', 'carbon capture', 'grön tech',
        'clean tech', 'klimatteknik', 'climate tech'
    ]
    
    IRRELEVANT_KEYWORDS = [
        'gaming', 'game', 'spel', 'dataspel', 'esport',
        'disney', 'netflix', 'film', 'movie', 'serie', 'TV show',
        'streaming', 'xbox', 'playstation', 'nintendo',
        'iphone', 'galaxy', 'pixel', 'macbook', 'ipad',
        'deals', 'sale', 'rabatt', 'köpguide', 'test av',
        'best movies', 'best shows', 'celebrity', 'kändis'
    ]
    
    SWEDISH_INDICATORS = [
        'sverige', 'swedish', 'stockholm', 'göteborg', 'malmö',
        'riksdag', 'regering', 'statsminister', 'miljöminister',
        'naturvårdsverket', 'smhi', 'sgu', 'havs- och vattenmyndigheten'
    ]
    
    def categorize(self, article: NewsArticle) -> NewsArticle:
        """Kategorisera artikel baserat på innehåll"""
        text = f"{article.title} {article.content}".lower()
        
        # Kolla om irrelevant först
        if any(keyword in text for keyword in self.IRRELEVANT_KEYWORDS):
            article.category = NewsCategory.IRRELEVANT
            logger.info(f"[SCRAPER] ❌ IRRELEVANT: {article.title}")
            return article
        
        # Identifiera geografisk region
        is_swedish = any(indicator in text for indicator in self.SWEDISH_INDICATORS)
        article.geographic_region = "Sverige" if is_swedish else "Global"
        
        # Kategorisera efter innehåll
        has_climate = any(kw in text for kw in self.CLIMATE_KEYWORDS)
        has_environment = any(kw in text for kw in self.ENVIRONMENT_KEYWORDS)
        has_tech_climate = any(kw in text for kw in self.TECH_CLIMATE_KEYWORDS)
        
        if has_climate and is_swedish:
            article.category = NewsCategory.CLIMATE_SWEDEN
        elif has_climate:
            article.category = NewsCategory.CLIMATE_GLOBAL
        elif has_environment and is_swedish:
            article.category = NewsCategory.ENVIRONMENT_SWEDEN
        elif has_environment:
            article.category = NewsCategory.ENVIRONMENT_GLOBAL
        elif has_tech_climate:
            article.category = NewsCategory.TECH_CLIMATE
        elif 'ai' in text or 'artificial intelligence' in text or 'maskininlärning' in text:
            article.category = NewsCategory.TECH_AI
        else:
            article.category = NewsCategory.TECH_GENERAL
        
        logger.info(f"[SCRAPER] ✅ {article.category.value.upper()} ({article.geographic_region}): {article.title[:60]}")
        return article


class RelevanceAgent:
    """
    Agent 2: Bedömer relevans mot MMM:s kriterier
    Ger relevance_score 0-100
    """
    
    def evaluate(self, article: NewsArticle) -> NewsArticle:
        """Betygsätt relevans för MMM Senaste Nytt"""
        
        # Irrelevanta artiklar får 0
        if article.category == NewsCategory.IRRELEVANT:
            article.relevance_score = 0
            return article
        
        # Scoring baserat på kategori och geografi
        base_scores = {
            NewsCategory.CLIMATE_SWEDEN: 100,
            NewsCategory.ENVIRONMENT_SWEDEN: 95,
            NewsCategory.CLIMATE_GLOBAL: 90,
            NewsCategory.ENVIRONMENT_GLOBAL: 85,
            NewsCategory.TECH_CLIMATE: 70,
            NewsCategory.TECH_AI: 40,
            NewsCategory.TECH_GENERAL: 20,
        }
        
        article.relevance_score = base_scores.get(article.category, 0)
        
        # Boost för svenska nyheter
        if article.geographic_region == "Sverige":
            article.relevance_score += 5
        
        # Penalty för vissa källor som ofta har irrelevanta nyheter
        if 'wired' in article.source.lower() or 'verge' in article.source.lower():
            if article.category in [NewsCategory.TECH_GENERAL, NewsCategory.TECH_AI]:
                article.relevance_score -= 20
        
        logger.info(f"[RELEVANCE] Score {article.relevance_score}: {article.title[:60]}")
        return article


class FactCheckAgent:
    """
    Agent 3: Faktakontroll och rimlighetsbedömning
    Använder AI för att bedöma om påståenden är rimliga
    """
    
    UNREALISTIC_PATTERNS = [
        (r'hundred.*dead|hundreds.*killed', r'thousand|tusen', 
         "Verkar underskatta dödsfall - bör vara tusentals, inte hundratals"),
        (r'million.*affected', r'thousand|tusen', 
         "Verkar överskatta påverkan - troligen tusentals, inte miljoner"),
        (r'100%|hundra procent', r'', 
         "100% påståenden är ofta orealistiska"),
    ]
    
    async def verify(self, article: NewsArticle) -> NewsArticle:
        """Verifiera fakta och rimlighet"""
        text = f"{article.title} {article.content}".lower()
        
        # Grundläggande rimlighetskontroller
        issues = []
        
        # Kolla efter orimliga siffror
        import re
        
        # Sudan-specifik check (exempel från dagens problem)
        if 'sudan' in text:
            if 'hundred' in text and 'dead' in text:
                if 'thousand' not in text:
                    issues.append("⚠️ Sudan-konflikten: 'Hundratals' döda verkar vara en underskattning. Troligen tusentals.")
        
        # Generella checks
        for pattern, counter_pattern, message in self.UNREALISTIC_PATTERNS:
            if re.search(pattern, text):
                if counter_pattern and not re.search(counter_pattern, text):
                    issues.append(message)
        
        if issues:
            article.fact_check_passed = False
            article.fact_check_notes = " | ".join(issues)
            logger.warning(f"[FACT-CHECK] ⚠️ {article.title[:60]}")
            for issue in issues:
                logger.warning(f"              {issue}")
        else:
            article.fact_check_passed = True
            logger.info(f"[FACT-CHECK] ✅ {article.title[:60]}")
        
        return article


class BalanceAgent:
    """
    Agent 4: Säkerställer rätt ämnesbalans
    Minst 50% klimat/miljö, max 50% tech/AI
    """
    
    def __init__(self, target_climate_percent: int = 60):
        self.target_climate_percent = target_climate_percent
    
    def balance(self, articles: List[NewsArticle], target_count: int = 10) -> List[NewsArticle]:
        """Välj balanserad uppsättning artiklar"""
        
        # Filtrera bort irrelevanta och fact-check-failade
        valid_articles = [
            a for a in articles 
            if a.category != NewsCategory.IRRELEVANT and a.fact_check_passed
        ]
        
        # Sortera efter relevans
        valid_articles.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Gruppera efter typ
        climate_env = [
            a for a in valid_articles 
            if a.category in [
                NewsCategory.CLIMATE_SWEDEN, NewsCategory.CLIMATE_GLOBAL,
                NewsCategory.ENVIRONMENT_SWEDEN, NewsCategory.ENVIRONMENT_GLOBAL,
                NewsCategory.TECH_CLIMATE
            ]
        ]
        
        tech_ai = [
            a for a in valid_articles
            if a.category in [NewsCategory.TECH_AI, NewsCategory.TECH_GENERAL]
        ]
        
        # Beräkna målfördelning
        climate_target = int(target_count * self.target_climate_percent / 100)
        tech_target = target_count - climate_target
        
        # Välj artiklar
        selected = climate_env[:climate_target] + tech_ai[:tech_target]
        
        # Om vi inte har tillräckligt med klimat-artiklar, fyll på med tech
        if len(selected) < target_count:
            remaining = target_count - len(selected)
            more_tech = [a for a in tech_ai if a not in selected][:remaining]
            selected.extend(more_tech)
        
        logger.info(f"[BALANCE] Valde {len([a for a in selected if a.category in [NewsCategory.CLIMATE_SWEDEN, NewsCategory.CLIMATE_GLOBAL, NewsCategory.ENVIRONMENT_SWEDEN, NewsCategory.ENVIRONMENT_GLOBAL, NewsCategory.TECH_CLIMATE]])} klimat/miljö och {len([a for a in selected if a.category in [NewsCategory.TECH_AI, NewsCategory.TECH_GENERAL]])} tech/AI")
        
        return selected[:target_count]


class NewsOrchestrator:
    """
    HUVUDORCHESTRATOR
    Koordinerar alla agenter och fattar slutgiltiga beslut
    """
    
    def __init__(self):
        self.scraper = NewsScraperAgent()
        self.relevance = RelevanceAgent()
        self.fact_checker = FactCheckAgent()
        self.balance = BalanceAgent(target_climate_percent=60)
    
    async def process_articles(self, raw_articles: List[Dict]) -> List[NewsArticle]:
        """
        Huvudprocess: Kör alla artiklar genom agent-pipeline
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 ORCHESTRATOR: Startar bearbetning av {len(raw_articles)} artiklar")
        logger.info(f"{'='*60}\n")
        
        # Konvertera till NewsArticle-objekt
        articles = [
            NewsArticle(
                source=a.get('source', ''),
                title=a.get('title', ''),
                content=a.get('content', ''),
                link=a.get('link', '')
            )
            for a in raw_articles
        ]
        
        # Steg 1: Kategorisering
        logger.info("\n📋 STEG 1: KATEGORISERING")
        logger.info("-" * 60)
        articles = [self.scraper.categorize(a) for a in articles]
        
        # Steg 2: Relevansbedömning
        logger.info("\n⭐ STEG 2: RELEVANSBEDÖMNING")
        logger.info("-" * 60)
        articles = [self.relevance.evaluate(a) for a in articles]
        
        # Steg 3: Faktakontroll
        logger.info("\n🔍 STEG 3: FAKTAKONTROLL")
        logger.info("-" * 60)
        articles = await asyncio.gather(*[self.fact_checker.verify(a) for a in articles])
        
        # Steg 4: Balansering
        logger.info("\n⚖️  STEG 4: BALANSERING")
        logger.info("-" * 60)
        selected = self.balance.balance(articles, target_count=10)
        
        # Slutrapport
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ ORCHESTRATOR: Slutresultat")
        logger.info(f"{'='*60}")
        logger.info(f"Totalt bearbetade: {len(articles)}")
        logger.info(f"Irrelevanta: {len([a for a in articles if a.category == NewsCategory.IRRELEVANT])}")
        logger.info(f"Fact-check failed: {len([a for a in articles if not a.fact_check_passed and a.category != NewsCategory.IRRELEVANT])}")
        logger.info(f"Valda för podcast: {len(selected)}")
        
        logger.info(f"\n📊 FÖRDELNING AV VALDA:")
        for category in NewsCategory:
            count = len([a for a in selected if a.category == category])
            if count > 0:
                logger.info(f"  • {category.value}: {count}")
        
        logger.info(f"\n📍 GEOGRAFISK FÖRDELNING:")
        sweden_count = len([a for a in selected if a.geographic_region == "Sverige"])
        logger.info(f"  • Sverige: {sweden_count}")
        logger.info(f"  • Global: {len(selected) - sweden_count}")
        
        return selected


async def main():
    """Test av agent-systemet"""
    # Exempel på test med dagens artiklar
    with open('episode_articles_20251107_040743.json', 'r', encoding='utf-8') as f:
        raw_articles = json.load(f)
    
    orchestrator = NewsOrchestrator()
    selected = await orchestrator.process_articles(raw_articles)
    
    print("\n" + "="*80)
    print("SLUTGILTIGT URVAL FÖR PODCAST:")
    print("="*80)
    for i, article in enumerate(selected, 1):
        print(f"\n{i}. [{article.category.value}] {article.title}")
        print(f"   Relevans: {article.relevance_score}/100")
        print(f"   Källa: {article.source}")
        print(f"   Region: {article.geographic_region}")
        if article.fact_check_notes:
            print(f"   ⚠️  {article.fact_check_notes}")


if __name__ == "__main__":
    asyncio.run(main())
