#!/usr/bin/env python3
"""
Komplett podcast-generator för MMM Senaste Nytt
Med musik-integration och riktig väderdata
"""

import os
import sys
import json
import logging
import shutil
import requests
import re
import html
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Lägg till modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from music_mixer import MusicMixer
from episode_history import EpisodeHistory

# Import Gemini TTS för förbättrad dialog
try:
    from gemini_tts_dialog import GeminiTTSDialogGenerator
    GEMINI_TTS_AVAILABLE = True
except ImportError as e:
    GEMINI_TTS_AVAILABLE = False

# Import KRITISK faktakontroll-agent
try:
    from news_fact_checker import NewsFactChecker
    FACT_CHECKER_AVAILABLE = True
except ImportError as e:
    FACT_CHECKER_AVAILABLE = False

# Import backup faktakontroll (fungerar utan AI)
try:
    from basic_fact_checker import BasicFactChecker, quick_fact_check
    BASIC_FACT_CHECKER_AVAILABLE = True
except ImportError as e:
    BASIC_FACT_CHECKER_AVAILABLE = False

# Import självkorrigerande faktakontroll
try:
    from self_correcting_fact_checker import SelfCorrectingFactChecker, auto_correct_podcast_content
    SELF_CORRECTING_AVAILABLE = True
except ImportError as e:
    SELF_CORRECTING_AVAILABLE = False

# Ladda miljövariabler
load_dotenv()
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Konfigurera logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('podcast_generation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

SWEDISH_WEEKDAYS = {
    'Monday': 'måndag',
    'Tuesday': 'tisdag',
    'Wednesday': 'onsdag',
    'Thursday': 'torsdag',
    'Friday': 'fredag',
    'Saturday': 'lördag',
    'Sunday': 'söndag'
}

SWEDISH_MONTHS = {
    1: 'januari',
    2: 'februari',
    3: 'mars',
    4: 'april',
    5: 'maj',
    6: 'juni',
    7: 'juli',
    8: 'augusti',
    9: 'september',
    10: 'oktober',
    11: 'november',
    12: 'december'
}

def get_swedish_weather() -> str:
    """Hämta aktuell väderdata från SMHI för svenska landskap"""
    try:
        # Importera SMHI-modulen
        from smhi_weather import SMHIWeatherService
        
        service = SMHIWeatherService()
        weather_summary = service.get_swedish_weather_summary()
        
        logger.info(f"[WEATHER] {weather_summary}")
        return weather_summary
            
    except Exception as e:
        logger.error(f"[WEATHER] Fel vid SMHI väder-hämtning: {e}")
        # Fallback till wttr.in om SMHI misslyckas
        try:
            logger.info("[WEATHER] Använder wttr.in som backup")
            # Svenska landskap med representativa städer - alla 4 regioner
            regions = [
                ("Götaland", "Goteborg"),
                ("Svealand", "Stockholm"),  
                ("Södra Norrland", "Sundsvall"),
                ("Norra Norrland", "Kiruna")
            ]
            
            weather_data = []
            for region_name, api_name in regions:
                try:
                    url = f"https://wttr.in/{api_name}?format=%C+%t"
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        weather_info = response.text.strip()
                        weather_data.append(f"{region_name}: {weather_info}")
                        
                except Exception:
                    continue
            
            if weather_data:
                weather_text = f"Vädret idag: {', '.join(weather_data)}"  # Visa alla regioner
                return weather_text
            else:
                return "Vädret idag: Varierande väderförhållanden över Sverige"
                
        except Exception:
            return "Vädret idag: Varierande väderförhållanden över Sverige"

def load_config() -> Dict:
    """Ladda konfiguration från sources.json"""
    try:
        with open('sources.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("[ERROR] sources.json hittades inte")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"[ERROR] Fel i sources.json: {e}")
        return {}

def get_openrouter_response(messages: List[Dict], model: str = "openai/gpt-4o-mini") -> str:
    """Skicka förfrågan till OpenRouter API"""
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY saknas i miljövariabler")
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/PontusDahlberg",
        "X-Title": "MMM Podcast Generator",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=90)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except requests.RequestException as e:
        logger.error(f"[ERROR] OpenRouter API error: {e}")
        raise

def generate_structured_podcast_content(weather_info: str) -> tuple[str, List[Dict]]:
    """Generera strukturerat podcast-innehåll med AI och riktig väderdata"""
    
    # Dagens datum för kontext
    today = datetime.now()
    date_str = today.strftime('%Y-%m-%d')
    weekday = today.strftime('%A')
    swedish_weekday = SWEDISH_WEEKDAYS.get(weekday, weekday)
    
    # Läs tidigare använda artiklar för upprepningsfilter (senaste 7 dagarna)
    used_articles = set()
    try:
        import glob
        article_files = glob.glob('episode_articles_*.json')
        
        # Filtrera på datum - bara senaste 7 dagarna
        cutoff_date = datetime.now() - timedelta(days=7)
        recent_files = []
        for article_file in article_files:
            try:
                # Extrahera datum från filnamn: episode_articles_20251014_190405.json
                date_str = article_file.split('_')[2]  # 20251014
                file_date = datetime.strptime(date_str, '%Y%m%d')
                if file_date >= cutoff_date:
                    recent_files.append(article_file)
            except (IndexError, ValueError):
                continue
        
        for article_file in recent_files:
            try:
                with open(article_file, 'r', encoding='utf-8') as f:
                    prev_articles = json.load(f)
                    for article in prev_articles:
                        # Använd länk som unik identifierare, eller titel om länk saknas
                        unique_id = article.get('link') or article.get('title', '').lower()
                        if unique_id:
                            used_articles.add(unique_id)
            except Exception as e:
                logger.warning(f"[HISTORY] Kunde inte läsa {article_file}: {e}")
        logger.info(f"[HISTORY] Laddade {len(used_articles)} tidigare använda artiklar för upprepningsfilter")
    except Exception as e:
        logger.warning(f"[HISTORY] Upprepningsfilter misslyckades: {e}")
    
    # Läs in tillgängliga artiklar för referens - ENDAST från seriösa nyhetskällor
    available_articles: List[Dict] = []
    climate_articles: List[Dict] = []  # Prioriterade klimat/miljö-artiklar
    tech_articles: List[Dict] = []     # Tech/AI-artiklar
    candidate_articles: List[Dict] = []
    repeat_articles: List[Dict] = []
    candidate_ids = set()
    
    # Lista över accepterade nyckelord för trovärdiga nyhetskällor (inkl. klimatkällor)
    trusted_sources = {
        'SVT', 'Dagens Nyheter', 'Svenska Dagbladet', 'BBC', 
        'Reuters', 'Guardian', 'Financial Times', 'AP News',
        'Dagens Industri', 'Computer Sweden', 'Ny Teknik', 'NyTeknik', 'Wired',
        'TechCrunch', 'Verge', 'Ars Technica', 'IEEE Spectrum',
        'Nature', 'Science', 'MIT Technology Review', 'Breakit', 'Digitala Verkligheter',
        'Miljö & Utveckling', 'Naturskyddsföreningen', 'Naturvårdsverket', 'Sveriges Natur',
        'Energimyndigheten', 'Aktuell Hållbarhet', 'SMHI', 'European Environment Agency',
        'EEA', 'European Commission', 'EU Commission', 'Eurostat', 'Europa.eu',
        'CleanTechnica', 'Climate Central'
    }
    
    # Klimat- och miljökällor för prioritering
    climate_sources = {
        'Miljö & Utveckling', 'Naturskyddsföreningen', 'Naturvårdsverket', 'Sveriges Natur',
        'Energimyndigheten', 'Aktuell Hållbarhet', 'SMHI', 'CleanTechnica', 'Climate Central',
        'European Environment Agency', 'EEA'
    }
    
    try:
        with open('scraped_content.json', 'r', encoding='utf-8') as f:
            scraped_data = json.load(f)
            for source_group in scraped_data:
                source_name = source_group.get('source', 'Okänd källa')
                
                # Kolla först om det är en trovärdig källa
                is_trusted = any(trusted.lower() in source_name.lower() for trusted in trusted_sources)
                if not is_trusted:
                    logger.info(f"[FILTER] Okänd källa, hoppar över: {source_name}")
                    continue
                
                # För "Digitala Verkligheter" - acceptera trots Facebook i namnet (kurerat AI-innehåll)
                if 'digitala verkligheter' not in source_name.lower():
                    # FILTRERA BORT sociala medier för andra källor
                    if any(social in source_name.lower() for social in ['facebook', 'twitter', 'instagram', 'tiktok', 'linkedin', 'youtube']):
                        logger.warning(f"[FILTER] Hoppar över social media källa: {source_name}")
                        continue
                
                logger.info(f"[FILTER] ✅ Accepterad källa: {source_name}")
                
                if 'items' in source_group:
                    for item in source_group['items'][:5]:  # Max 5 per källa
                        if item.get('link') and item.get('title'):
                            # Dubbelkolla att länken inte går till sociala medier (förutom för Digitala Verkligheter)
                            link_url = item.get('link', '')
                            if 'digitala verkligheter' not in source_name.lower():
                                if any(social in link_url.lower() for social in ['facebook.com', 'twitter.com', 'instagram.com', 'tiktok.com']):
                                    logger.warning(f"[FILTER] Hoppar över social media länk: {link_url}")
                                    continue

                            article_id = item.get('link') or item.get('title', '').lower()
                            if not article_id or article_id in candidate_ids:
                                continue

                            is_repeat = article_id in used_articles
                            if is_repeat:
                                logger.info(f"[FILTER] Upprepad artikel hittad: {item.get('title', '')[:50]}...")

                            # Innehållsfilter: bara relevanta ämnen för teknik/AI/klimat-podcast
                            title_text = item.get('title', '').lower()
                            content_text = item.get('content', '').lower()
                            combined_text = title_text + " " + content_text

                            # Relevanta nyckelord för MMM Senaste Nytt
                            relevant_keywords = [
                                # AI & Teknik
                                'ai', 'artificiell intelligens', 'machine learning', 'maskininlärning',
                                'teknik', 'teknologi', 'innovation', 'forskning', 'vetenskap',
                                'datorer', 'mjukvara', 'app', 'digital', 'internet', 'cybersäkerhet',
                                # Klimat & Miljö (utökad lista)
                                'klimat', 'miljö', 'hållbarhet', 'förnybar energi', 'koldioxid', 'co2',
                                'växthusgaser', 'global uppvärmning', 'klimatförändringar', 'paris',
                                'elbil', 'solenergi', 'vindkraft', 'batterier', 'elektricitet',
                                'återvinning', 'cirkulär ekonomi', 'biodiversitet', 'ekosystem',
                                'naturskydd', 'energieffektivitet', 'fossila bränslen', 'elkraft',
                                'väder', 'temperatur', 'havsnivå', 'smältning', 'is', 'torka'
                            ]

                            # Irrelevanta ämnen som vi ska filtrera bort (UTÖKAD LISTA)
                            irrelevant_keywords = [
                                'våld', 'mord', 'knivskuren', 'skjutning', 'död', 'dödad',
                                'krig', 'konflikt', 'gaza', 'palestina', 'palestinska', 'israel', 'ukraina',
                                'knark', 'droger', 'narkotika', 'kriminell', 'polis', 'häktad',
                                'val', 'politik', 'parti', 'regering', 'minister', 'kyrka', 'kyrkovalet',
                                'sport', 'fotboll', 'hockey', 'motorsport', 'racing', 'trump', 'putin',
                                'satellitbilder', 'förstör', 'byar', 'musiktävling', 'köttallergi', 'allergi',
                                # Extra politik-filter
                                'avgång', 'avgångsersättning', 'riksdagen', 'motion', 'landslag', 'fotboll',
                                'asllani', 'hatt', 'politisk', 'politiker', 'debatt', 'omröstning',
                                # Extra irrelevanta ämnen
                                'rökdykning', 'räddningstjänst', 'brandkår', 'teckenspråk', 'språk',
                                'kultur', 'bok', 'författare', 'adolescence', 'gruvdrift', 'malmberget'
                            ]

                            has_irrelevant = any(keyword in combined_text for keyword in irrelevant_keywords)
                            if has_irrelevant:
                                logger.info(f"[FILTER] Filtrerar bort irrelevant artikel: {title_text[:50]}...")
                                continue

                            article_info = {
                                'source': source_name,
                                'title': item['title'][:100],
                                'content': item.get('content', '')[:300],
                                'link': item['link']
                            }
                            candidate_ids.add(article_id)
                            candidate_articles.append(article_info)

                            if is_repeat:
                                repeat_articles.append(article_info)
                                continue

                            has_relevant = any(keyword in combined_text for keyword in relevant_keywords)
                            if not has_relevant:
                                logger.info(f"[FILTER] Filtrerar bort icke-relevant artikel: {title_text[:50]}...")
                                continue

                            # Kontrollera om det är en klimat-artikel
                            climate_keywords = [
                                'klimat', 'miljö', 'hållbarhet', 'förnybar energi', 'koldioxid', 'co2',
                                'växthusgaser', 'global uppvärmning', 'klimatförändringar', 'paris',
                                'elbil', 'solenergi', 'vindkraft', 'batterier', 'elektricitet',
                                'återvinning', 'cirkulär ekonomi', 'biodiversitet', 'ekosystem',
                                'naturskydd', 'energieffektivitet', 'fossila bränslen', 'elkraft',
                                'väder', 'temperatur', 'havsnivå', 'smältning', 'is', 'torka'
                            ]
                            is_climate = any(kw in combined_text for kw in climate_keywords)
                            is_climate_source = any(src.lower() in source_name.lower() for src in climate_sources)
                            
                            if is_climate or is_climate_source:
                                climate_articles.append(article_info)
                                logger.info(f"[FILTER] ✅ Klimat/miljö-artikel: {title_text[:50]}...")
                            else:
                                tech_articles.append(article_info)
                                logger.info(f"[FILTER] Tech/AI-artikel: {title_text[:50]}...")
    except Exception as e:
        logger.warning(f"[CONTENT] Kunde inte läsa artikeldata: {e}")
    
    # Bygg balanserad artikellista: MINST 50% klimat/miljö
    logger.info(f"[BALANCE] Klimat/miljö: {len(climate_articles)}, Tech/AI: {len(tech_articles)}")
    
    # Ta 60% klimat, 40% tech för att säkerställa balans
    climate_count = max(6, int(len(climate_articles) * 0.6)) if climate_articles else 0
    tech_count = max(4, int(len(tech_articles) * 0.4)) if tech_articles else 0
    
    available_articles = climate_articles[:climate_count] + tech_articles[:tech_count]
    logger.info(f"[BALANCE] Balanserad lista: {len(climate_articles[:climate_count])} klimat + {len(tech_articles[:tech_count])} tech = {len(available_articles)} totalt")
    
    if len(available_articles) < 6 and repeat_articles:
        needed = 6 - len(available_articles)
        logger.warning(f"[FILTER] Fyller på med {min(needed, len(repeat_articles))} artiklar från senaste dagarna")
        available_articles.extend(repeat_articles[:needed])

    if not available_articles and candidate_articles:
        logger.warning("[FILTER] Inga nya artiklar klarade filtren - använder fallback från trovärdiga källor")
        available_articles = candidate_articles[:8]

    # Skapa artikelreferenser för AI
    article_refs = ""
    if available_articles:
        article_refs = "\n\nTILLGÄNGLIGA ARTIKLAR ATT REFERERA TILL:\n"
        for i, article in enumerate(available_articles[:10], 1):
            article_refs += f"{i}. {article['source']}: {article['title']}\n   Innehåll: {article['content']}\n   [Referera som: {article['source']}]\n\n"
    
    prompt = f"""Skapa ett KOMPLETT och DETALJERAT manus för dagens avsnitt av "MMM Senaste Nytt" - en svensk daglig nyhetspodcast om teknik, AI och klimat.

DATUM: {date_str} ({swedish_weekday})
VÄDER: {weather_info}
LÄNGD: Absolut mål är 10 minuter (minst 1800-2200 ord för talat innehåll)
VÄRDAR: Lisa (kvinnlig, professionell men vänlig) och Pelle (manlig, nyfiken och engagerad)

{article_refs}

DETALJERAD STRUKTUR:
1. INTRO & VÄLKOMST (90-120 sekunder) - Inkludera RIKTIG väderinfo från "{weather_info}"
2. INNEHÅLLSÖVERSIKT (60-90 sekunder) - Detaljerad genomgång av alla ämnen
3. HUVUDNYHETER (6-7 minuter) - 5-6 nyheter med djup analys och dialog  
4. DJUP DISKUSSION/ANALYS (2-3 minuter) - Lisa och Pelle diskuterar trender och framtid
5. SAMMANFATTNING (60-90 sekunder) - Detaljerad recap av alla ämnen
6. OUTRO & MMM-KOPPLING (60-90 sekunder) - STARK koppling till huvudpodden "Människa Maskin Miljö"

INNEHÅLLSKRAV OCH ÄMNESFÖRDELNING:
- Lisa säger "MMM Senaste Nytt" naturligt och professionellt (inte överdrivet)
- Använd RIKTIG väderdata: "{weather_info}" - inte påhittade kommentarer om "fin dag i Stockholm"
- Minst 6 konkreta nyheter från svenska och internationella källor
- OBLIGATORISK ÄMNESFÖRDELNING (mycket viktigt för balans):
  * MINST 50% av nyheterna MÅSTE handla om KLIMAT, MILJÖ och HÅLLBARHET
  * Maximalt 50% får handla om AI och teknologi (inte klimatrelaterad)
  * Prioritera SVENSKA klimat- och miljönyheter när de finns tillgängliga
  * Exempel: Om du har 6 nyheter, MINST 3 ska vara klimat/miljö
- Varje nyhet ska vara minst 150-200 ord inklusive diskussion
- Lisa och Pelle ska ha naturliga konversationer med följdfrågor
- Inkludera siffror, fakta och konkreta exempel
- Nämn specifika företag, forskare eller organisationer

KÄLLHÄNVISNING - MYCKET VIKTIGT:
- ANVÄND ENDAST artiklarna listade ovan som källor för dina nyheter - ALDRIG sociala medier eller opålitliga källor
- VARJE nyhet MÅSTE baseras på en specifik artikel från seriösa medier (SVT, DN, BBC, Reuters etc.)
- FÖRBJUDET: Facebook, Twitter/X, Instagram, TikTok, YouTube eller andra sociala medier som källor
- Referera tydligt: "SVT Nyheter rapporterar att...", "BBC News skriver att...", "Reuters meddelar att..."
- Specifika personer MÅSTE namnges när de finns i artiklarna (t.ex. "Miljöminister Romina Pourmokhtari säger...", "Enligt statsminister Ulf kristersson...")
- Konkreta detaljer MÅSTE tas från artiklarna - påhitta ALDRIG fakta
- När möjligt: använd siffror och fakta från artiklarna
- Om information saknas i artiklarna - säg det tydligt ("detaljerna är ännu inte kända", "ingen tidsplan har presenterats")
- Undvik vaga termer - var specifik baserat på vad som faktiskt står i artiklarna
- Lyssnarna ska kunna förstå att nyheten kommer från en etablerad, trovärdig nyhetskälla

OUTRO-KRAV (MYCKET VIKTIGT):
- INGEN teasing av "nästa avsnitt" 
- INGA påhittade lyssnarfrågor
- STARK koppling till huvudpodden "Människa Maskin Miljö"
- Förklara att MMM Senaste Nytt är en del av Människa Maskin Miljö-familjen
- Uppmana lyssnare att kolla in huvudpodden för djupare analyser
- OBLIGATORISK AI-BRASKLAPP: Lisa och Pelle ska ödmjukt förklara att de är <phoneme alphabet="ipa" ph="ɑːːiːː">AI</phoneme>-röster och att information kan innehålla fel, hänvisa till länkarna i avsnittsinformationen för verifiering

DIALOGREGLER:
- Använd naturliga övergångar: "Det påminner mig om...", "Apropå det...", "Interessant nog..."
- Lisa och Pelle ska ibland avbryta varandra naturligt
- Inkludera korta pauser för eftertanke: "Hmm, det är en bra poäng..."
- Använd svenska uttryck och vardagligt språk
- Variera meningslängderna för naturligt flyt
- KRITISKT: Varje replik måste logiskt följa föregående - ingen får svara på något som inte sagts ännu
- KRITISKT: Om någon nämner en siffra/statistik, måste den först ha presenterats i tidigare replik
- Kontrollera att alla hänvisningar ("det", "den siffran", "som du sa") faktiskt refererar till något som redan sagts

FORMAT: Skriv ENDAST som ren dialog med "Talarnamn: Text" - INGEN markdown eller formatering!
FÖRBJUDET: **, ##, ---, ###, rubriker, markeringar, lyssnarfrågor, "nästa avsnitt" - bara ren dialog!

EXEMPEL INTRO:
Lisa: Hej och välkommen till MMM Senaste Nytt! Jag heter Lisa.
Pelle: Och jag heter Pelle. Idag är det {swedish_weekday} den {today.strftime('%d')} {today.strftime('%B').lower()}, och {weather_info.lower()}.
Lisa: Ja, det stämmer! Men vi har mycket spännande att prata om idag inom teknik, AI och klimat.

VIKTIGT: Endast dialog - inga rubriker eller formatering! Bara "Namn: Text" rad för rad.

Skapa nu ett KOMPLETT och LÅNGT manus för dagens avsnitt - kom ihåg minst 1800 ord:"""

    messages = [{"role": "user", "content": prompt}]
    
    try:
        content = get_openrouter_response(messages)
        logger.info("[AI] Genererade podcast-innehåll med väderdata")
        return content, available_articles
    except Exception as e:
        logger.error(f"[ERROR] Kunde inte generera AI-innehåll: {e}")
        # Fallback till mock-innehåll
        return generate_fallback_content(date_str, swedish_weekday, weather_info), available_articles

def generate_fallback_content(date_str: str, weekday: str, weather_info: str) -> str:
    """Fallback-innehåll om AI inte fungerar"""
    return f"""Lisa: Hej och välkommen till MMM Senaste Nytt! Jag heter Lisa.

Pelle: Och jag heter Pelle. Idag är det {weekday} den {datetime.now().strftime('%d')} oktober, och {weather_info.lower()}.

Lisa: Precis! Vi har mycket att prata om idag inom teknik, AI och klimat.

Pelle: Vi börjar med att OpenAI har lanserat en förbättrad version av GPT-4 som de kallar GPT-4 Turbo. Modellen är inte bara snabbare, utan också betydligt billigare att använda för utvecklare.

Lisa: Det är verkligen stora nyheter, Pelle. Vad tror du det betyder för svenska företag som använder AI?

Pelle: Jag tror det kommer att demokratisera AI-användningen. Mindre företag kommer nu ha råd att bygga avancerade AI-lösningar.

Lisa: Spännande! Vi fortsätter med klimatnyheter. Tesla har presenterat sina nya 4680-batterier som påstås ha 50% bättre energidensitet.

Pelle: Det är riktigt intressanta nyheter. Bättre batterier är nyckeln till både elbilar och energilagring.

Lisa: För att sammanfatta har vi pratat om OpenAI:s nya modell och Teslas batteriteknik.

Pelle: Det här avsnittet av MMM Senaste Nytt är en del av vårt större program Människa Maskin Miljö, där vi går djupare in på hur teknik, klimat och samhälle påverkar varandra.

Lisa: Tack för att ni lyssnade! Vi hörs imorgon med fler nyheter."""

def clean_text_for_tts(text: str) -> str:
    """Ta bort markdown-formattering och andra tecken som inte ska läsas upp"""
    # Ta bort markdown-formattering
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **text** -> text
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *text* -> text
    text = re.sub(r'#{1,6}\s*', '', text)           # ### headings -> 
    text = re.sub(r'---+', '', text)                # --- -> 
    text = re.sub(r'^\s*[-*+]\s*', '', text, flags=re.MULTILINE)  # list items
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # [text](link) -> text
    
    # Ta bort andra formattering
    text = re.sub(r'`([^`]+)`', r'\1', text)        # `code` -> code
    text = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', text)  # __text__ -> text
    
    # Rensa extra whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def split_long_text_for_tts(text: str, speaker: str, max_bytes: int = 4000) -> List[Dict]:
    """Dela upp lång text i TTS-kompatibla segment"""
    segments = []
    
    # Om texten är kort nog, returnera som ett segment
    if len(text.encode('utf-8')) <= max_bytes:
        return [{'speaker': speaker, 'text': text}]
    
    # Dela vid meningar först
    sentences = re.split(r'(?<=[.!?])\s+', text)
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence_bytes = len(sentence.encode('utf-8'))
        
        # Om en enskild mening är för lång, dela den hårdare
        if sentence_bytes > max_bytes:
            # Spara nuvarande chunk först
            if current_chunk:
                segments.append({
                    'speaker': speaker,
                    'text': ' '.join(current_chunk).strip()
                })
                current_chunk = []
                current_size = 0
            
            # Dela den långa meningen vid komma eller ord
            words = sentence.split()
            word_chunk = []
            word_size = 0
            
            for word in words:
                word_bytes = len((word + ' ').encode('utf-8'))
                if word_size + word_bytes > max_bytes and word_chunk:
                    segments.append({
                        'speaker': speaker,
                        'text': ' '.join(word_chunk).strip()
                    })
                    word_chunk = [word]
                    word_size = word_bytes
                else:
                    word_chunk.append(word)
                    word_size += word_bytes
            
            if word_chunk:
                segments.append({
                    'speaker': speaker,
                    'text': ' '.join(word_chunk).strip()
                })
        else:
            # Kontrollera om vi kan lägga till meningen
            if current_size + sentence_bytes > max_bytes and current_chunk:
                segments.append({
                    'speaker': speaker,
                    'text': ' '.join(current_chunk).strip()
                })
                current_chunk = [sentence]
                current_size = sentence_bytes
            else:
                current_chunk.append(sentence)
                current_size += sentence_bytes
    
    # Lägg till sista chunk
    if current_chunk:
        segments.append({
            'speaker': speaker,
            'text': ' '.join(current_chunk).strip()
        })
    
    return segments

def parse_podcast_text(text: str) -> List[Dict]:
    """Parsa podcast-text i segment med talare och repliker"""
    segments = []
    lines = text.strip().split('\n')
    
    current_speaker = None
    current_text = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Hoppa över rena formattering-rader
        if line.startswith('#') or line.startswith('---') or line.startswith('### '):
            continue
            
        # Identifiera talare-rader (med eller utan markdown-formattering)
        if ':' in line and len(line.split(':', 1)) == 2:
            speaker_part, text_part = line.split(':', 1)
            
            # Rensa speaker-namnet från formattering
            speaker_name = clean_text_for_tts(speaker_part).strip()
            
            # Hoppa över om det inte ser ut som ett talare-namn
            if not speaker_name or len(speaker_name.split()) > 2:
                if current_speaker:
                    current_text.append(clean_text_for_tts(line))
                continue
            
            # Spara föregående segment
            if current_speaker and current_text:
                clean_text = ' '.join(current_text).strip()
                if clean_text:  # Endast om det finns text
                    # Dela upp långa segment för TTS-kompatibilitet (max 4000 bytes)
                    split_segments = split_long_text_for_tts(clean_text, current_speaker)
                    segments.extend(split_segments)
            
            # Starta nytt segment
            current_speaker = speaker_name
            text_part_clean = clean_text_for_tts(text_part).strip()
            current_text = [text_part_clean] if text_part_clean else []
        else:
            # Fortsätt med samma talare
            if current_speaker:
                clean_line = clean_text_for_tts(line)
                if clean_line:  # Endast lägg till om det finns text
                    current_text.append(clean_line)
    
    # Lägg till sista segmentet
    if current_speaker and current_text:
        clean_text = ' '.join(current_text).strip()
        if clean_text:  # Endast om det finns text
            # Dela upp långa segment för TTS-kompatibilitet (max 4000 bytes)
            split_segments = split_long_text_for_tts(clean_text, current_speaker)
            segments.extend(split_segments)
    
    return segments

def generate_audio_with_gemini_dialog(script_content: str, weather_info: str, output_file: str) -> bool:
    """Generera audio med Gemini TTS för naturlig dialog mellan Lisa och Pelle"""
    if not GEMINI_TTS_AVAILABLE:
        logger.info("[AUDIO] Gemini TTS inte tillgänglig, använder standard-metod")
        return False
    
    try:
        logger.info("[AUDIO] Genererar naturlig dialog med Gemini TTS...")
        
        generator = GeminiTTSDialogGenerator()
        
        # Skapa dialog-script från innehåll
        dialog_script = generator.create_dialog_script(script_content, weather_info)
        logger.info("[AUDIO] Dialog-script skapat för Lisa och Pelle")
        
        # Generera audio med freeform dialog
        success = generator.synthesize_dialog_freeform(
            dialog_script=dialog_script,
            output_file=output_file
        )
        
        if success:
            logger.info(f"[AUDIO] ✅ Gemini TTS dialog sparad: {output_file}")
            return True
        else:
            logger.warning("[AUDIO] Gemini TTS misslyckades, faller tillbaka till standard")
            return False
            
    except Exception as e:
        logger.error(f"[AUDIO] Gemini TTS fel: {e}")
        logger.info("[AUDIO] Faller tillbaka till standard TTS")
        return False

def generate_audio_google_cloud(segments: List[Dict], output_file: str) -> bool:
    """Generera audio med Google Cloud TTS (fallback-metod)"""
    try:
        # Använd rätt TTS-klass
        from google_cloud_tts import GoogleCloudTTS
        
        # Konvertera segments till rätt format
        audio_segments = []
        for i, segment in enumerate(segments):
            speaker = segment['speaker'].lower()
            
            # Mappa talare till röster
            if 'lisa' in speaker:
                voice = 'lisa'
            elif 'pelle' in speaker:
                voice = 'pelle'
            else:
                # Alternerande röster
                voice = 'lisa' if i % 2 == 0 else 'pelle'
            
            audio_segments.append({
                'voice': voice,
                'text': segment['text']
            })
        
        # Skapa TTS-instans och generera audio
        tts = GoogleCloudTTS()
        audio_file = tts.generate_podcast_audio(audio_segments)
        
        if audio_file and os.path.exists(audio_file):
            shutil.move(audio_file, output_file)
            logger.info(f"[TTS] Audio genererad: {output_file}")
            return True
        else:
            logger.error("[ERROR] TTS-generering misslyckades")
            return False
            
    except Exception as e:
        logger.error(f"[ERROR] TTS-fel: {e}")
        return False

def add_music_to_podcast(audio_file: str) -> str:
    """Lägg till musik och bryggkor till podcast med MusicMixer"""
    try:
        logger.info("[MUSIC] Lägger till musik och bryggkor...")
        
        # Skapa en MusicMixer-instans
        mixer = MusicMixer()
        
        # Skanna alla mp3-filer i music-mappen automatiskt
        music_dir = "audio/music"
        available_music = []
        
        if os.path.exists(music_dir):
            for filename in os.listdir(music_dir):
                if filename.lower().endswith('.mp3'):
                    full_path = os.path.join(music_dir, filename)
                    available_music.append(full_path)
        
        logger.info(f"[MUSIC] Hittade {len(available_music)} musikfiler: {[os.path.basename(f) for f in available_music]}")
        
        if not available_music:
            logger.warning("[MUSIC] Inga musikfiler hittades")
            return audio_file
            
        # Skapa varierad musikmix för hela avsnittet
        import random
        music_output = audio_file.replace('.mp3', '_with_music.mp3')
        
        # Nya förbättrade musikmixning med variation
        success = mixer.create_varied_music_background(
            speech_file=audio_file,
            available_music=available_music,
            output_file=music_output,
            music_volume=-15,  # Låg volym i dB
            segment_duration=60,  # Byt musik var 60:e sekund
            fade_duration=3000    # 3 sekunder crossfade mellan låtar
        )
        
        if success and os.path.exists(music_output):
            # Ersätt original med musikversion
            shutil.move(music_output, audio_file)
            logger.info(f"[MUSIC] Musik tillagd till {audio_file}")
            return audio_file
        else:
            logger.warning("[MUSIC] Kunde inte lägga till musik, använder original")
            return audio_file
            
    except Exception as e:
        logger.error(f"[MUSIC] Fel vid musiktillägg: {e}")
        return audio_file  # Returnera original om musik misslyckas


def enforce_intro_date(script_text: str, weekday: str, day: int, month: str) -> str:
    """Replace incorrect intro date phrases with the actual Swedish date."""
    if not script_text:
        return script_text

    def _replace_intro(match: re.Match) -> str:
        intro_line = match.group(0)
        comma_index = intro_line.find(',')
        suffix = intro_line[comma_index:] if comma_index != -1 else ''
        logger.info("[SCRIPT] Uppdaterar intro-datum till dagens datum")
        return f"Idag är det {weekday} den {day} {month}{suffix}"

    return re.sub(r"Idag är det[^\n]*", _replace_intro, script_text, count=1)


def clean_xml_text(text: Optional[str]) -> str:
    """Sanitize text for safe XML output"""
    if not text:
        return ""

    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', str(text))
    normalized = html.unescape(cleaned)
    return html.escape(normalized, quote=True)


def generate_github_rss(episodes_data: List[Dict], base_url: str) -> str:
    """Generera RSS-feed för GitHub Pages"""
    rss_items = []
    
    for episode in episodes_data:
        # Hantera båda gamla (date) och nya (pub_date) format
        if 'pub_date' in episode:
            pub_date = episode['pub_date']  # Redan i rätt format
        elif 'date' in episode:
            pub_date = datetime.strptime(episode['date'], '%Y-%m-%d').strftime('%a, %d %b %Y %H:%M:%S +0000')
        else:
            pub_date = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')
        
        # Hantera både gamla och nya format för audio URL och storlek
        if 'audio_url' in episode:
            # Nytt format från episodhistorik
            audio_url = episode['audio_url']
            file_size = episode.get('file_size', 7000000)
            guid = episode.get('guid', audio_url)
        else:
            # Gammalt format från direct generation
            audio_url = f"{base_url}/audio/{episode['filename']}"
            file_size = episode.get('size', 7000000)
            guid = audio_url
        
        safe_title = clean_xml_text(episode.get('title', ''))
        safe_description = clean_xml_text(episode.get('description', ''))
        safe_audio_url = html.escape(audio_url, quote=True)
        safe_guid = clean_xml_text(guid)

        rss_items.append(f"""        <item>
            <title>{safe_title}</title>
            <description>{safe_description}</description>
            <pubDate>{pub_date}</pubDate>
            <enclosure url="{safe_audio_url}" length="{file_size}" type="audio/mpeg"/>
            <guid>{safe_guid}</guid>
        </item>""")
    
    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
    <channel>
        <title>MMM Senaste Nytt - MÄNNISKA MASKIN MILJÖ</title>
        <description>Dagliga nyheter från världen av människa, maskin och miljö - med Lisa och Pelle. En del av Människa Maskin Miljö-familjen.</description>
        <link>{base_url}</link>
        <language>sv-SE</language>
        <itunes:category text="Technology"/>
        <itunes:category text="Science"/>
        <itunes:category text="News"/>
        <itunes:explicit>false</itunes:explicit>
        <itunes:author>Pontus Dahlberg</itunes:author>
        <itunes:summary>Daglig nyhetspodcast om AI, teknik och klimat - en del av Människa Maskin Miljö-familjen</itunes:summary>
        <itunes:owner>
            <itunes:name>Pontus Dahlberg</itunes:name>
            <itunes:email>pontus.dahlberg@gmail.com</itunes:email>
        </itunes:owner>
        <itunes:image href="{base_url}/cover.jpg"/>
        <lastBuildDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}</lastBuildDate>
        {''.join(rss_items)}
    </channel>
</rss>"""
    
    return rss_content

def main():
    """Huvudfunktion för komplett podcast-generering med musik och väder"""
    logger.info("[PODCAST] Startar MMM Senaste Nytt med musik och väder...")
    
    # Log Gemini TTS status after logger is initialized
    if GEMINI_TTS_AVAILABLE:
        logger.info("[SYSTEM] Gemini TTS tillgänglig för naturlig dialog")
    else:
        logger.warning("[SYSTEM] Gemini TTS inte tillgänglig - använder standard TTS")
    
    # Log Fact Checker status
    if FACT_CHECKER_AVAILABLE:
        logger.info("[SYSTEM] 🛡️ KRITISK faktakontroll-agent aktiverad för säkerhet")
    else:
        logger.error("[SYSTEM] ⚠️ VARNING: Faktakontroll-agent inte tillgänglig - RISK FÖR FELAKTIG INFO!")
    
    try:
        # Hämta väderdata först
        logger.info("[WEATHER] Hämtar aktuell väderdata...")
        weather_info = get_swedish_weather()
        logger.info(f"[WEATHER] {weather_info}")
        
        # Ladda konfiguration
        config = load_config()
        
        # Generera datum och filnamn
        today = datetime.now()
        timestamp = today.strftime('%Y%m%d_%H%M%S')
        
        # Skapa output-mappar
        os.makedirs('audio', exist_ok=True)
        os.makedirs('public/audio', exist_ok=True)
        
        # Generera strukturerat podcast-innehåll med riktig väderdata
        logger.info("[AI] Genererar strukturerat podcast-innehåll...")
        podcast_content, referenced_articles = generate_structured_podcast_content(weather_info)

        weekday_swedish = SWEDISH_WEEKDAYS.get(today.strftime('%A'), today.strftime('%A'))
        month_swedish = SWEDISH_MONTHS.get(today.month, today.strftime('%B').lower())
        podcast_content = enforce_intro_date(podcast_content, weekday_swedish, today.day, month_swedish)
        
        # Spara manus för referens
        script_path = f"podcast_script_{timestamp}.txt"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(podcast_content)
        logger.info(f"[SCRIPT] Manus sparat: {script_path}")
        
        # Spara artikelreferenser för senare användning
        articles_path = f"episode_articles_{timestamp}.json"
        with open(articles_path, 'w', encoding='utf-8') as f:
            json.dump(referenced_articles, f, indent=2, ensure_ascii=False)
        logger.info(f"[ARTICLES] Artikelreferenser sparade: {articles_path}")
        
        # 🛡️ SJÄLVKORRIGERANDE FAKTAKONTROLL - Automatisk korrigering av problem
        final_podcast_content = podcast_content
        max_correction_attempts = 3
        
        for correction_attempt in range(max_correction_attempts):
            logger.info(f"[FACT-CHECK] 🛡️ Faktakontroll försök {correction_attempt + 1}/{max_correction_attempts}")
            
            # Grundläggande faktakontroll först (snabbast)
            fact_check_passed = False
            if BASIC_FACT_CHECKER_AVAILABLE:
                basic_checker = BasicFactChecker()
                basic_result = basic_checker.basic_fact_check(final_podcast_content)
                
                if basic_result['safe_to_publish']:
                    # Visa varningar men godkänn ändå
                    warnings = basic_result.get('warnings', [])
                    if warnings:
                        logger.info(f"[FACT-CHECK] ✅ Faktakontroll godkänd med varningar: {warnings}")
                    else:
                        logger.info("[FACT-CHECK] ✅ Faktakontroll godkänd helt")
                    fact_check_passed = True
                    break
                else:
                    critical_issues = basic_result.get('critical_issues', [])
                    warnings = basic_result.get('warnings', [])
                    logger.error(f"[FACT-CHECK] ❌ Kritiska problem hittade: {critical_issues}")
                    if warnings:
                        logger.info(f"[FACT-CHECK] ℹ️ Varningar (blockerar inte): {warnings}")
                    
                    # Försök automatisk korrigering
                    if SELF_CORRECTING_AVAILABLE and correction_attempt < max_correction_attempts - 1:
                        logger.info("[FACT-CHECK] 🔧 Startar automatisk korrigering...")
                        
                        corrected_content, correction_success = auto_correct_podcast_content(
                            final_podcast_content, basic_result.get('critical_issues', [])
                        )
                        
                        if correction_success:
                            logger.info("[FACT-CHECK] ✅ Automatisk korrigering lyckades!")
                            final_podcast_content = corrected_content
                            
                            # Spara korrigerat manus
                            corrected_script_path = f"podcast_script_{timestamp}_corrected_v{correction_attempt + 1}.txt"
                            with open(corrected_script_path, 'w', encoding='utf-8') as f:
                                f.write(final_podcast_content)
                            logger.info(f"[SCRIPT] Korrigerat manus sparat: {corrected_script_path}")
                            continue
                        else:
                            logger.warning("[FACT-CHECK] ⚠️ Automatisk korrigering misslyckades")
                    else:
                        logger.warning("[FACT-CHECK] ⚠️ Självkorrigering inte tillgänglig")
            
            # Om vi når hit har korrigering misslyckats eller är sista försöket
            break
        
        # Final kontroll
        if not fact_check_passed:
            logger.error("🚨 PUBLICERING STOPPAD - FAKTAKONTROLL MISSLYCKADES!")
            
            # Spara rapport för manuell granskning
            final_report_path = f"fact_check_failed_{timestamp}.txt"
            with open(final_report_path, 'w', encoding='utf-8') as f:
                f.write("FAKTAKONTROLL MISSLYCKADES\n")
                f.write(f"Datum: {datetime.now().isoformat()}\n")
                f.write(f"Försök gjorda: {correction_attempt + 1}\n\n")
                if 'basic_result' in locals():
                    f.write("SENASTE PROBLEM:\n")
                    for issue in basic_result['issues_found']:
                        f.write(f"- {issue}\n")
            
            print(f"\n🚨 SÄKERHETSVARNING: Automatisk korrigering misslyckades!")
            print(f"Rapport sparad: {final_report_path}")
            print("Manuell granskning krävs. Se MANUAL_FACT_CHECK_GUIDE.md")
            return False
        else:
            logger.info("[FACT-CHECK] ✅ Faktakontroll godkänd - säkert att publicera")
            # Uppdatera innehållet om det korrigerades
            if final_podcast_content != podcast_content:
                logger.info("[FACT-CHECK] 📝 Använder automatiskt korrigerat innehåll")
                podcast_content = final_podcast_content
        
        # Parsa innehållet i segment
        segments = parse_podcast_text(podcast_content)
        logger.info(f"[PARSE] Hittade {len(segments)} segment att generera audio för")
        
        # Räkna ord för att uppskatta längd
        total_words = sum(len(segment['text'].split()) for segment in segments)
        estimated_minutes = total_words / 150  # Ungefär 150 ord per minut i tal
        logger.info(f"[ESTIMATE] {total_words} ord, uppskattad längd: {estimated_minutes:.1f} minuter")
        
        # Generera filnamn
        audio_filename = f"MMM_senaste_nytt_{timestamp}.mp3"
        audio_filepath = os.path.join('audio', audio_filename)
        
        # Försök först med Gemini TTS för naturlig dialog
        logger.info("[TTS] Försöker generera naturlig dialog med Gemini TTS...")
        gemini_success = generate_audio_with_gemini_dialog(podcast_content, weather_info, audio_filepath)
        
        if not gemini_success:
            # Fallback till standard Google Cloud TTS
            logger.info("[TTS] Använder standard Google Cloud TTS som fallback...")
            success = generate_audio_google_cloud(segments, audio_filepath)
            
            if not success:
                logger.error("[ERROR] Audio-generering misslyckades")
                return False
        else:
            logger.info("[TTS] ✅ Naturlig dialog genererad med Gemini TTS!")
        
        # Lägg till musik och bryggkor
        audio_filepath = add_music_to_podcast(audio_filepath)
        
        # Kopiera till public/audio för GitHub Pages
        public_audio_path = os.path.join('public', 'audio', audio_filename)
        shutil.copy2(audio_filepath, public_audio_path)
        logger.info(f"[FILES] Kopierade audio till {public_audio_path}")
        
        # Skapa episode data med artiklar som faktiskt refererades i avsnittet
        file_size = os.path.getsize(audio_filepath)
        
        # Debug: Kolla om vi har artiklar att visa
        logger.info(f"[RSS] Antal tillgängliga artiklar: {len(referenced_articles)}")
        
        # Använd artiklar som faktiskt refererades under genereringen
        article_links = []
        for i, article in enumerate(referenced_articles[:6]):  # Max 6 artiklar
            logger.info(f"[RSS] Artikel {i+1}: {article.get('source', 'N/A')} - {article.get('title', 'N/A')[:50]}...")
            if article.get('link') and article.get('title'):
                # Korta titlar för bättre läsbarhet
                short_title = article['title'][:60] + "..." if len(article['title']) > 60 else article['title']
                source_name = article.get('source', 'Okänd källa')
                article_links.append(f"{source_name}: {short_title}\n  {article['link']}")
        
        sources_text = ""
        if article_links:
            sources_text = f"\n\nKällor som refereras i detta avsnitt:\n• " + "\n• ".join(article_links)
            logger.info(f"[RSS] Lade till {len(article_links)} källor i RSS-beskrivning")
        else:
            logger.warning("[RSS] Inga källor att visa i RSS-beskrivning!")
            # Fallback: använd sources.json som backup
            try:
                config = load_config()
                if config and 'sources' in config:
                    fallback_sources = [s['name'] for s in config['sources'][:4] if s.get('enabled', True)]
                    if fallback_sources:
                        sources_text = f"\n\nKällor: {', '.join(fallback_sources)}"
                        logger.info(f"[RSS] Använder fallback-källor: {fallback_sources}")
            except Exception as e:
                logger.error(f"[RSS] Fel vid fallback-källor: {e}")
        
        month_swedish = SWEDISH_MONTHS[today.month]
        weekday_swedish = SWEDISH_WEEKDAYS.get(today.strftime('%A'), today.strftime('%A'))
        
        episode_data = {
            'title': f"MMM Senaste Nytt - {today.day} {month_swedish} {today.year}",
            'description': f"Dagens nyheter inom AI, teknik och klimat - {weekday_swedish} den {today.day} {month_swedish} {today.year}. Med detaljerade källhänvisningar från svenska och internationella medier.{sources_text}",
            'date': today.strftime('%Y-%m-%d'),
            'filename': audio_filename,
            'size': file_size,
            'duration': f"{estimated_minutes:.0f}:00"
        }
        
        # Lägg till episod till historik och generera RSS-feed med alla episoder
        logger.info("[HISTORY] Lägger till episod till historik...")
        history = EpisodeHistory()
        all_episodes = history.add_episode(episode_data)
        
        # Generera RSS-feed med alla episoder (max 10 senaste för RSS-prestanda)
        base_url = "https://pontusdahlberg.github.io/morgonpodden"
        recent_episodes = all_episodes[:10]  # Ta bara 10 senaste för RSS-feed
        rss_content = generate_github_rss(recent_episodes, base_url)
        
        # Spara RSS-feed
        rss_path = os.path.join('public', 'feed.xml')
        with open(rss_path, 'w', encoding='utf-8') as f:
            f.write(rss_content)
        logger.info(f"[RSS] RSS-feed sparad med {len(recent_episodes)} episoder: {rss_path}")
        
        # Logga framgång
        logger.info("[SUCCESS] Komplett podcast-generering slutförd!")
        logger.info(f"[AUDIO] Audio: {audio_filepath}")
        logger.info(f"[SCRIPT] Manus: {script_path}")
        logger.info(f"[RSS] RSS: {rss_path}")
        logger.info(f"[WEATHER] Väder: {weather_info}")
        logger.info(f"[STATS] Segment: {len(segments)}, Ord: {total_words}, Längd: ~{estimated_minutes:.1f} min")
        logger.info(f"[GITHUB] GitHub Pages URL: {base_url}")
        logger.info(f"[FEED] RSS URL: {base_url}/feed.xml")
        
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Oväntat fel: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)