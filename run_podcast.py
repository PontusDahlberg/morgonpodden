#!/usr/bin/env python3
"""
Huvudscript för automatisk podcast-generering
Människa Maskin Miljö - Weekly AI & Climate Podcast
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List
from dotenv import load_dotenv

# Lägg till emotion analyzer och musik-mixer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from music_mixer import MusicMixer

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
        'ELEVENLABS_VOICE_ID_SANNA',
        'ELEVENLABS_VOICE_ID_GEORGE',
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
    
    # Skapa en sammanfattning av alla nyheter
    news_summary = ""
    for item in news_data:
        title = item.get('title', 'Okänd titel')
        description = item.get('description', 'Ingen beskrivning')
        source = item.get('source', 'Okänd källa')
        news_summary += f"- {title} ({source}): {description}\n"
    
    week_info = get_week_info()
    
    # OpenRouter API anrop
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        logger.warning("⚠️ OpenRouter API key saknas, använder mock-data")
        return generate_mock_summary(week_info)
    
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://manniska-maskin-miljo.com',
            'X-Title': 'Människa Maskin Miljö Podcast'
        }
        
        prompt = f"""Du är värd för den svenska podcasten "Människa Maskin Miljö" som fokuserar på teknik, AI och miljö.

Skapa ett engagerande podcast-manus för vecka {week_info['week']}, {week_info['year']} baserat på dessa nyheter:

{news_summary}

VIKTIGT - Skriv ENDAST ren taltext utan:
- Inga namn på talare (som "Sanna:", "George:")
- Inga stage directions (som "(entusiastiskt)", "(allvarlig ton)")
- Inga manus-markeringar eller rubriker
- Bara ren text som ska läsas upp

Krav för manuset:
- Skriv på svenska
- Börja med välkomst: "Välkommen till Människa Maskin Miljö, vecka {week_info['week']}!"
- Skriv som en sammanhängande berättelse utan karaktärsnamn
- Variera tonen naturligt: professionell, spännande, allvarlig eller vänlig
- Dela upp i naturliga stycken (5-8 stycken) för röstväxling
- Avsluta med "Det var allt för denna vecka. Tack för att ni lyssnade!"
- Totalt cirka 3-4 minuter läsning (2000-2500 ord)

Exempel på rätt format:
Välkommen till Människa Maskin Miljö, vecka 38!

Den här veckan har vi spännande utvecklingar inom artificiell intelligens...

Nu kommer vi till mer allvarliga nyheter om cybersäkerhet...

Fokusera på svenska nyheter och koppla till miljö/teknik-perspektiv även för internationella nyheter."""

        payload = {
            'model': 'anthropic/claude-3.5-sonnet',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 3000,
            'temperature': 0.7
        }
        
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_content = result['choices'][0]['message']['content']
            
            # Rensa text från stage directions och karaktärsnamn
            cleaned_content = clean_script_text(ai_content)
            
            logger.info("✅ AI-sammanfattning genererad med OpenRouter")
            return cleaned_content
        else:
            logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
            return generate_mock_summary(week_info)
            
    except Exception as e:
        logger.error(f"Error generating AI summary: {e}")
        return generate_mock_summary(week_info)

def generate_mock_summary(week_info: Dict) -> str:
    """Fallback mock summary om AI-generering misslyckas"""
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
    return mock_summary.strip()

def clean_script_text(text: str) -> str:
    """Rensa manus-text från stage directions och karaktärsnamn"""
    import re
    
    # Ta bort manus-headers och metadata
    text = re.sub(r'\[.*?\]', '', text)  # [PODCAST-MANUS: ...] 
    text = re.sub(r'---.*?---', '', text, flags=re.DOTALL)  # --- metadata ---
    
    # Ta bort karaktärsnamn i början av meningar
    text = re.sub(r'^(Sanna|George):\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n(Sanna|George):\s*', '\n', text)
    
    # Ta bort stage directions i parenteser
    text = re.sub(r'\([^)]*\)', '', text)
    
    # Ta bort karaktärsnamn följt av colon mitt i text
    text = re.sub(r'\b(Sanna|George):\s*', '', text)
    
    # VIKTIGT: Bevara styckeindelning! Rensa försiktigt
    # Ta bort endast överflödiga whitespace, men bevara styckeindelningar
    text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 newlines
    text = re.sub(r'^[ \t]+', '', text, flags=re.MULTILINE)  # Leading spaces/tabs only
    text = text.strip()
    
    return text

def generate_audio(text: str, config: Dict) -> str:
    """Generera audio med ElevenLabs och intelligenta musik-bryggkor"""
    logger.info("🎵 Genererar audio med ElevenLabs (Emotion-baserat + musik-bryggkor)...")
    
    try:
        # Dela upp texten för olika röster med emotion analysis
        sections = split_text_for_voices(text)
        
        week_info = get_week_info()
        audio_filename = f"audio/episode_{week_info['week']}_{week_info['year']}.mp3"
        
        # Skapa audio-mapp
        os.makedirs('audio', exist_ok=True)
        os.makedirs('audio/temp', exist_ok=True)
        
        # Initialisera musik-mixer
        music_mixer = MusicMixer()
        
        # Generera individuella tal-segment (utan musik)
        segment_data = []
        for i, section in enumerate(sections):
            voice_id = section['voice_id']
            text_content = section['text']
            voice_name = section['voice_name']
            emotion = section['emotion']
            voice_settings = section['voice_settings']
            
            logger.info(f"🎤 Segment {i+1}: {voice_name} ({emotion}) - {text_content[:50]}...")
            
            # Generera tal-audio
            audio_data = generate_elevenlabs_audio_with_settings(text_content, voice_id, voice_settings)
            
            # Spara tal-segment
            speech_file = f"audio/temp/segment_{i+1}_speech.mp3"
            with open(speech_file, 'wb') as f:
                f.write(audio_data)
            
            segment_data.append({
                'speech_file': speech_file,
                'emotion': emotion,
                'voice_name': voice_name
            })
        
        # Skapa podcast med musik-bryggkor istället för konstant bakgrund
        success = music_mixer.create_podcast_with_musical_bridges(segment_data, audio_filename)
        
        if not success:
            # Fallback: kombinera utan musik
            logger.warning("⚠️ Using simple speech combination without music")
            combine_audio_segments_simple([s['speech_file'] for s in segment_data], audio_filename)
        
        # Rensa temp-filer
        cleanup_temp_files('audio/temp')
        
        logger.info(f"✅ Audio-fil med musik-bryggkor skapad: {audio_filename} ({len(sections)} segment(s))")
        return audio_filename
        
    except Exception as e:
        logger.error(f"❌ Fel vid musik-bryggkor audio-generering: {e}")
        # Fallback till enkel generering
        return generate_simple_audio(text, config)

def combine_audio_segments_simple(segment_files: List[str], output_file: str) -> None:
    """Enkel kombination av audio-segment utan musik (fallback)"""
    try:
        from pydub import AudioSegment
        
        combined = AudioSegment.empty()
        for segment_file in segment_files:
            if os.path.exists(segment_file):
                segment = AudioSegment.from_file(segment_file)
                combined += segment
        
        combined.export(output_file, format="mp3")
        logger.info(f"✅ Simple audio combination completed: {output_file}")
        
    except Exception as e:
        logger.error(f"Error in simple combination: {e}")
        # Ultra-fallback: binär kombinering
        with open(output_file, 'wb') as outf:
            for segment_file in segment_files:
                if os.path.exists(segment_file):
                    with open(segment_file, 'rb') as inf:
                        outf.write(inf.read())

def cleanup_temp_files(temp_dir: str) -> None:
    """Rensa temporära filer"""
    try:
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"🧹 Cleaned up temp files: {temp_dir}")
    except Exception as e:
        logger.warning(f"Could not clean temp files: {e}")

def generate_simple_audio(text: str, config: Dict) -> str:
    """Fallback: Enkel audio-generering utan emotion analysis"""
    logger.info("🔄 Använder enkel audio-generering som fallback...")
    
    week_info = get_week_info()
    audio_filename = f"audio/episode_{week_info['week']}_{week_info['year']}.mp3"
    os.makedirs('audio', exist_ok=True)
    
    try:
        sanna_voice = os.getenv('ELEVENLABS_VOICE_ID_SANNA')
        audio_data = generate_elevenlabs_audio(text, sanna_voice)
        
        with open(audio_filename, 'wb') as f:
            f.write(audio_data)
        
        logger.info(f"✅ Fallback audio-fil skapad: {audio_filename}")
        return audio_filename
    except Exception as e:
        logger.error(f"❌ Även fallback misslyckades: {e}")
        # Ultimate fallback
        with open(audio_filename, 'wb') as f:
            f.write(b'MOCK_AUDIO_DATA')
        return audio_filename

def generate_elevenlabs_audio_with_settings(text: str, voice_id: str, voice_settings: Dict) -> bytes:
    """Generera audio med specifika voice settings"""
    import requests
    
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        raise ValueError("ElevenLabs API key saknas")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": voice_settings
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"ElevenLabs API fel: {response.status_code} - {response.text}")

def split_text_for_voices(text: str) -> List[Dict]:
    """Dela upp text för olika röster med emotion analysis"""
    from emotion_analyzer import split_content_by_emotion
    
    # Använd intelligent emotion-baserad uppdelning
    segments = split_content_by_emotion(text)
    
    # Om ingen segmentering, fallback till enkel uppdelning
    if not segments:
        sanna_voice = os.getenv('ELEVENLABS_VOICE_ID_SANNA')
        segments = [{
            'text': text, 
            'voice_id': sanna_voice,
            'voice_name': 'Sanna',
            'emotion': 'professional',
            'voice_settings': {
                'stability': 0.5,
                'similarity_boost': 0.85,
                'style': 0.5,
                'use_speaker_boost': True
            }
        }]
    
    return segments

def generate_elevenlabs_audio(text: str, voice_id: str) -> bytes:
    """Generera audio med ElevenLabs API"""
    import requests
    
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        raise ValueError("ElevenLabs API key saknas")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    # Förbättrade voice settings för mer energisk och professionell podcast
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.4,           # Lägre för mer variation och energi
            "similarity_boost": 0.85,   # Högre för bättre röstlikhet
            "style": 0.6,              # Högre för mer uttrycksfull röst
            "use_speaker_boost": True   # Extra boost för klarhet
        }
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        logger.info(f"✅ Audio genererat för röst {voice_id} (förbättrade inställningar)")
        return response.content
    else:
        raise Exception(f"ElevenLabs API fel: {response.status_code} - {response.text}")

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
