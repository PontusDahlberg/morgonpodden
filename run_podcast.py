#!/usr/bin/env python3
"""
Huvudscript för automatisk podcast-generering
Människa Maskin Miljö - Weekly AI & Climate Podcast
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from dotenv import load_dotenv

# Ladda miljövariabler från .env
load_dotenv()

# Lägg till src-mappen i Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Importera våra moduler
try:
    from cloudflare_uploader import CloudflareUploader
    from generate_rss import generate_and_upload_rss
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("🔧 Kontrollera att alla filer finns i src/ mappen")
    sys.exit(1)

# Konfigurera logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('podcast_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config() -> Dict:
    """Ladda konfiguration från sources.json"""
    try:
        with open('sources.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("❌ sources.json not found")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error parsing sources.json: {e}")
        raise

def check_environment() -> bool:
    """Kontrollera att alla nödvändiga miljövariabler finns"""
    required_vars = [
        'OPENROUTER_API_KEY',
        'ELEVENLABS_API_KEY', 
        'ELEVENLABS_VOICE_ID',
        'CLOUDFLARE_API_TOKEN',
        'CLOUDFLARE_R2_BUCKET',
        'CLOUDFLARE_R2_PUBLIC_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    logger.info("✅ All environment variables found")
    return True

def get_week_info() -> Dict:
    """Hämta information om aktuell vecka"""
    now = datetime.now()
    
    # Hitta senaste onsdag
    days_since_wednesday = (now.weekday() - 2) % 7
    if days_since_wednesday == 0 and now.hour < 7:
        # Om det är onsdag innan 07:00, använd förra onsdagen
        days_since_wednesday = 7
    
    last_wednesday = now - timedelta(days=days_since_wednesday)
    
    # Beräkna veckonummer
    week_number = last_wednesday.isocalendar()[1]
    year = last_wednesday.year
    
    return {
        'week': str(week_number),
        'year': year,
        'date': last_wednesday.strftime('%Y-%m-%d'),
        'pub_date': last_wednesday.strftime('%a, %d %b %Y 07:00:00 +0200')
    }

def scrape_news_sources(config: Dict) -> List[Dict]:
    """Scrapa nyheter från konfigurerade källor"""
    logger.info("📰 Scrapar svenska nyhetskällor...")
    
    # TODO: Implementera RSS-scraping från sources.json
    # För nu, använd mock data för testing
    week_info = get_week_info()
    
    mock_news = [
        {
            "title": "AI-genombrott inom klimatmodellering",
            "source": "Computer Sweden", 
            "summary": "Nya AI-modeller kan förutsäga klimatförändringar med 90% noggrannhet."
        },
        {
            "title": "Svenska gröna investeringar når rekordnivåer",
            "source": "Dagens Nyheter",
            "summary": "Investeringar i förnybar energi ökade med 150% under 2025."
        },
        {
            "title": "ChatGPT får nya miljöfunktioner",
            "source": "Ny Teknik",
            "summary": "OpenAI lanserar klimat-AI för att hjälpa företag minska utsläpp."
        }
    ]
    
    logger.info(f"✅ Hittade {len(mock_news)} nyhetskällor")
    return mock_news

def generate_ai_summary(news_data: List[Dict], config: Dict) -> str:
    """Generera AI-sammanfattning med OpenRouter"""
    logger.info("🤖 Genererar AI-sammanfattning...")
    
    # TODO: Implementera OpenRouter API-anrop
    # För nu, använd mock summary för testing
    week_info = get_week_info()
    
    mock_summary = f"""
    Välkommen till Människa Maskin Miljö, vecka {week_info['week']}! 

    Den här veckan har vi spännande utvecklingar inom AI och klimatteknik. 
    
    Först ut: AI-genombrott inom klimatmodellering. Nya maskininlärningsmodeller 
    kan nu förutsäga klimatförändringar med 90 procent noggrannhet, vilket ger 
    oss bättre verktyg för att planera framtiden.
    
    Vidare ser vi rekordnivåer för svenska gröna investeringar. Satsningar på 
    förnybar energi ökade med 150 procent under 2025, vilket visar att Sverige 
    ligger i framkant av den gröna omställningen.
    
    Slutligen har ChatGPT fått nya miljöfunktioner. OpenAI lanserar nu klimat-AI 
    som hjälper företag att minska sina utsläpp genom intelligent analys och 
    rekommendationer.
    
    Det var allt för den här veckan. Vi hörs nästa onsdag i Människa Maskin Miljö!
    """
    
    logger.info("✅ AI-sammanfattning genererad")
    return mock_summary.strip()

def generate_audio(text: str, config: Dict) -> str:
    """Generera audio med ElevenLabs"""
    logger.info("🎵 Genererar audio med ElevenLabs...")
    
    # TODO: Implementera ElevenLabs API-anrop
    # För nu, skapa mock audio-fil för testing
    week_info = get_week_info()
    audio_filename = f"audio/episode_{week_info['week']}_{week_info['year']}.mp3"
    
    # Skapa audio-mapp
    os.makedirs('audio', exist_ok=True)
    
    # Skapa mock audio-fil (tom fil för testing)
    with open(audio_filename, 'wb') as f:
        # I verkligheten skulle detta vara MP3-data från ElevenLabs
        f.write(b'MOCK_AUDIO_DATA')
    
    logger.info(f"✅ Audio-fil skapad: {audio_filename}")
    return audio_filename

def create_episode_metadata(week_info: Dict, summary: str, audio_url: str) -> Dict:
    """Skapa metadata för episoden"""
    return {
        "week": week_info['week'],
        "year": week_info['year'], 
        "date": week_info['date'],
        "description": f"Vecka {week_info['week']}: {summary[:200]}...",
        "audio_url": audio_url,
        "guid": f"mmm-{week_info['year']}-w{week_info['week']}",
        "pub_date": week_info['pub_date'],
        "file_size": 15000000,  # 15MB
        "duration": "12:30"
    }

def main():
    """Huvudfunktion för podcast-generering"""
    logger.info("🚀 Startar Människa Maskin Miljö podcast-generering...")
    
    try:
        # 1. Kontrollera miljö
        if not check_environment():
            sys.exit(1)
        
        # 2. Ladda konfiguration
        config = load_config()
        logger.info("✅ Konfiguration laddad")
        
        # 3. Hämta veckoinfo
        week_info = get_week_info()
        logger.info(f"📅 Genererar för vecka {week_info['week']}, {week_info['year']}")
        
        # 4. Scrapa nyheter
        news_data = scrape_news_sources(config)
        
        # 5. Generera AI-sammanfattning
        summary = generate_ai_summary(news_data, config)
        
        # 6. Generera audio
        audio_file = generate_audio(summary, config)
        
        # 7. Ladda upp audio till R2
        logger.info("☁️ Laddar upp audio till Cloudflare R2...")
        uploader = CloudflareUploader()
        
        if not uploader.test_connection():
            raise Exception("R2 connection failed")
        
        # Upload audio
        remote_audio_name = f"episodes/{week_info['year']}-w{week_info['week']}.mp3"
        audio_url = uploader.upload_file(audio_file, remote_audio_name)
        
        if not audio_url:
            raise Exception("Audio upload failed")
        
        logger.info(f"✅ Audio uploaded: {audio_url}")
        
        # 8. Skapa episod-metadata
        episode_data = create_episode_metadata(week_info, summary, audio_url)
        
        # 9. Generera och ladda upp RSS
        rss_config = {
            "publicUrl": os.getenv('CLOUDFLARE_R2_PUBLIC_URL')
        }
        
        rss_result = generate_and_upload_rss([episode_data], rss_config, upload_to_r2=True)
        
        if rss_result.get('public_url'):
            logger.info(f"✅ RSS feed updated: {rss_result['public_url']}")
        else:
            raise Exception("RSS upload failed")
        
        # 10. Slutrapport
        logger.info("🎉 Podcast-generering lyckades!")
        logger.info(f"📡 RSS Feed: {rss_result['public_url']}")
        logger.info(f"🎵 Episode: {audio_url}")
        logger.info(f"📅 Vecka: {week_info['week']}/{week_info['year']}")
        
        print("✅ PODCAST GENERATION COMPLETE!")
        print(f"📡 RSS: {rss_result['public_url']}")
        
    except Exception as e:
        logger.error(f"❌ Podcast generation failed: {e}")
        print(f"❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
