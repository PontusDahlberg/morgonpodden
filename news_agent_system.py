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
    
    AI_KEYWORDS = [
        'artificial intelligence', 'machine learning', 'maskininlärning',
        'deep learning', 'neural network', 'chatgpt', 'openai',
        'ai model', 'ai-model', 'generative ai', 'llm',
        'large language model', 'ai algorithm', 'ai-driven',
        'robotics', 'autonomous', 'autonom', 'ai safety',
        'ai regulation', 'ai-reglering', 'ai ethics'
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
        has_ai = any(kw in text for kw in self.AI_KEYWORDS)
        
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
        elif has_ai:
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

        # Redaktionell linje: undvik att driva kärnkraft som "lösning".
        # Vi tillåter kärnkraftsnyheter, men sänker prioriteten om de inte tydligt handlar om problem/konsekvenser.
        text = f"{article.title} {article.content}".lower()
        mentions_nuclear = any(k in text for k in ['kärnkraft', 'karnkraft', 'nuclear', 'smr', 'reaktor', 'reactor'])
        nuclear_problem_context = any(k in text for k in ['dyr', 'kostnad', 'försening', 'försen', 'slutförvar', 'avfall', 'waste', 'delay', 'overrun'])
        if mentions_nuclear and not nuclear_problem_context:
            article.relevance_score -= 10
        
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


class NewsQualityAgent:
    """
    Agent 5: Djupgranskning av relevans och nyhetsvärde
    Filtrerar bort "falska positiva" som innehåller klimatord men inte är klimatnyheter
    """
    
    # Nyheter som INTE är relevanta trots klimat-keywords
    FALSE_POSITIVE_PATTERNS = [
        # Krig och konflikt (även om "energy sites" nämns)
        (r'ukrain|russia.*attack|missile.*strike|war.*dead|military.*target', 
         "Krigsnyheter är inte klimatnyheter, även om energianläggningar nämns"),
        
        # Geopolitik utan klimatfokus
        (r'sanction.*russia|trump.*orbán|political.*deal.*energy',
         "Geopolitisk energipolitik utan klimatvinkel är inte relevant"),
        
        # Lokala consumer-nyheter (USA-specifika produkter/tjänster)
        (r'homes.*in.*california|homes.*in.*texas|menifee|us households.*install',
         "Lokala consumer-nyheter från USA är inte relevanta för svensk klimatpodd"),
        
        # Flyginställningar pga väder (inte klimatbeteende)
        (r'flight.*cancel.*weather|airport.*close.*storm|travel.*disrupt.*snow',
         "Flyginställningar pga väder är inte klimatnyheter om folk inte ändrar beteende"),
        
        # Mat och hälsa (sockerarter, allergier, etc)
        (r'sockerar|sugar.*health|food.*allerg|diet.*advice',
         "Mat- och hälsonyheter är inte relevanta för klimatpodd"),
        
        # Sport och underhållning
        (r'fotboll|hockey|sport|music.*award|film.*festival',
         "Sport och underhållning är aldrig relevant"),
        
        # Allmän politik utan klimatfokus
        (r'riksdag.*motion|minister.*avgång|election.*result|political.*scandal',
         "Allmän politik utan klimatfokus är inte relevant"),

        # Brott och våld (aldrig relevant för tech/klimat-podd)
        (r'våldtäkt|misshandel|mord|skjutning|knivskuren|brottsoffer|rape|assault|murder|polisinsats',
         "Våldsbrott är aldrig relevanta för denna podd"),

        # Personliga anekdoter och familjehistorier (ofta från Reddit/sociala medier)
        (r'min familj|min fru|min man|min dotter|min son|my family|my wife|my husband|reddit|flashback|familjeliv|jag känner|min upplevelse',
         "Personliga anekdoter och forumtrådar är inte nyheter"),

        # Jakt och viltvård (specifikt vargfrågan som ofta dyker upp felaktigt)
        (r'varg|jakt|licensjakt|älgjakt|wolf|hunting',
         "Jakt- och viltvårdsfrågor är inte relevanta för tech/klimat"),
    ]
    
    # Mönster för VERKLIGT relevanta klimatnyheter
    TRUE_CLIMATE_PATTERNS = [
        r'klimatmål|klimatavtal|cop\d+|ipcc.*rapport',  # Klimatpolitik
        r'koldioxid.*minskning|utsläpp.*reducera|co2.*capture',  # Utsläppsminskningar
        r'förnybar.*energi.*sverige|solceller.*sverige|vindkraft.*sverige',  # Svensk energiomställning
        r'elbilar.*försäljning|elbil.*miljö|batteriteknik.*genombrott',  # Verklig tech-innovation
        r'naturskydd.*beslut|nationalpark|artutrotning|biodiversitet.*kris',  # Naturvård
        r'väder.*extrem.*öka|torka.*värre|översvämning.*klimat',  # Klimateffekter
    ]
    
    def evaluate_quality(self, article: NewsArticle) -> tuple[bool, str]:
        """
        Bedöm om artikeln verkligen är relevant
        Returns: (is_quality, reason)
        """
        # Support both NewsArticle objects and dicts
        if isinstance(article, dict):
            title = article.get('title', '')
            content = article.get('content', '')
            category = article.get('category', '')
            text = f"{title} {content}".lower()
        else:
            title = article.title
            content = article.content
            category = article.category
            text = f"{title} {content}".lower()
        
        # Om kategoriserad som irrelevant, godkänn den bedömningen
        if category == NewsCategory.IRRELEVANT or category == 'irrelevant':
            return (True, "Korrekt kategoriserad som irrelevant")
        
        # Kolla efter false positives
        for pattern, reason in self.FALSE_POSITIVE_PATTERNS:
            import re
            if re.search(pattern, text):
                return (False, reason)
        
        # Om kategoriserad som klimat, verifiera att det VERKLIGEN är klimat
        climate_categories = [NewsCategory.CLIMATE_SWEDEN, NewsCategory.CLIMATE_GLOBAL, 
                             NewsCategory.ENVIRONMENT_SWEDEN, NewsCategory.ENVIRONMENT_GLOBAL,
                             'climate_sweden', 'climate_global', 'environment_sweden', 'environment_global']
        if category in climate_categories:
            # Kräv minst ETT true climate pattern
            import re
            has_true_climate = any(re.search(pattern, text) for pattern in self.TRUE_CLIMATE_PATTERNS)
            
            if not has_true_climate:
                # Om inget true climate pattern hittades, kräv svensk relevans eller forskning
                geo_region = article.get('geographic_region', '') if isinstance(article, dict) else article.geographic_region
                if geo_region == "Sverige":
                    return (True, "Svensk klimat/miljö-nyhet godkänd")
                elif any(word in text for word in ['forskning', 'research', 'studie', 'study', 'rapport', 'report']):
                    return (True, "Klimatforskning godkänd")
                else:
                    return (False, "Innehåller klimatord men saknar verklig klimatfokus")
        
        return (True, "Kvalitetsgodkänd")


class BalanceAgent:
    """
    Agent 5: Säkerställer rätt ämnesbalans
    Lika delar klimat, tech och AI (33% vardera)
    """
    
    def __init__(self):
        pass
    
    def balance(self, articles: List[NewsArticle], target_count: int = 10) -> List[NewsArticle]:
        """Välj balanserad uppsättning artiklar - lika delar klimat, tech, AI"""
        
        # Filtrera bort irrelevanta och fact-check-failade
        valid_articles = [
            a for a in articles 
            if a.category != NewsCategory.IRRELEVANT and a.fact_check_passed
        ]
        
        # Sortera efter relevans
        valid_articles.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Gruppera i 3 kategorier
        climate_env = [
            a for a in valid_articles 
            if a.category in [
                NewsCategory.CLIMATE_SWEDEN, NewsCategory.CLIMATE_GLOBAL,
                NewsCategory.ENVIRONMENT_SWEDEN, NewsCategory.ENVIRONMENT_GLOBAL
            ]
        ]
        
        tech_general = [
            a for a in valid_articles
            if a.category == NewsCategory.TECH_GENERAL
        ]
        
        ai_articles = [
            a for a in valid_articles
            if a.category == NewsCategory.TECH_AI
        ]
        
        # TECH_CLIMATE räknas som klimat
        tech_climate = [
            a for a in valid_articles
            if a.category == NewsCategory.TECH_CLIMATE
        ]
        climate_env.extend(tech_climate)
        
        # Beräkna målfördelning (lika delar, med avrundning)
        per_category = target_count // 3  # 3 delar för 10 artiklar = 3 vardera
        remainder = target_count % 3       # Rest att fördela
        
        climate_target = per_category + (1 if remainder > 0 else 0)  # 4
        tech_target = per_category + (1 if remainder > 1 else 0)      # 3
        ai_target = per_category                                       # 3
        
        # Välj artiklar från varje kategori
        selected_climate = climate_env[:climate_target]
        selected_tech = tech_general[:tech_target]
        selected_ai = ai_articles[:ai_target]
        
        selected = selected_climate + selected_tech + selected_ai
        
        # Om någon kategori har för få artiklar, fyll på från andra kategorier
        if len(selected) < target_count:
            remaining = target_count - len(selected)
            
            # Försök fylla på med artiklar från andra kategorier (högst rankade)
            all_unused = [a for a in valid_articles if a not in selected]
            all_unused.sort(key=lambda x: x.relevance_score, reverse=True)
            selected.extend(all_unused[:remaining])
        
        # Logga fördelning
        climate_count = len([a for a in selected if a.category in [NewsCategory.CLIMATE_SWEDEN, NewsCategory.CLIMATE_GLOBAL, NewsCategory.ENVIRONMENT_SWEDEN, NewsCategory.ENVIRONMENT_GLOBAL, NewsCategory.TECH_CLIMATE]])
        tech_count = len([a for a in selected if a.category == NewsCategory.TECH_GENERAL])
        ai_count = len([a for a in selected if a.category == NewsCategory.TECH_AI])
        
        logger.info(f"[BALANCE] Valde {climate_count} klimat/miljö, {tech_count} tech, {ai_count} AI")
        
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
        self.quality = NewsQualityAgent()
        self.balance = BalanceAgent()
    
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
        
        # Steg 4: Kvalitetsgranskning (NY!)
        logger.info("\n🎯 STEG 4: KVALITETSGRANSKNING")
        logger.info("-" * 60)
        quality_filtered = []
        for article in articles:
            is_quality, reason = self.quality.evaluate_quality(article)
            if is_quality:
                quality_filtered.append(article)
                logger.info(f"[QUALITY] ✅ {article.title[:60]}")
            else:
                logger.warning(f"[QUALITY] ❌ {article.title[:60]}")
                logger.warning(f"           Reason: {reason}")
        articles = quality_filtered
        
        # Steg 5: Balansering
        logger.info("\n⚖️  STEG 5: BALANSERING")
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
