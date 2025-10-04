#!/usr/bin/env python3
"""
GitHub-first podcast generering - utan Cloudflare-beroenden
Människa Maskin Miljö - Weekly AI & Climate Podcast
"""

import os
import sys
import json
import logging
import requests
import shutil
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

# Konfigurera logging med UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('podcast_generation.log', encoding='utf-8'),
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
        logger.error("❌ sources.json hittades inte")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"❌ Fel i sources.json: {e}")
        return {}

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
            
        # Identifiera talare-rader (startar med stor bokstav följt av kolon)
        if ':' in line and len(line.split(':', 1)) == 2:
            speaker_part, text_part = line.split(':', 1)
            speaker_name = speaker_part.strip()
            
            # Om vi har en föregående talare, spara det segmentet
            if current_speaker and current_text:
                segments.append({
                    'speaker': current_speaker,
                    'text': ' '.join(current_text).strip()
                })
            
            # Starta nytt segment
            current_speaker = speaker_name
            current_text = [text_part.strip()] if text_part.strip() else []
        else:
            # Fortsätt med samma talare
            if current_speaker:
                current_text.append(line)
    
    # Lägg till sista segmentet
    if current_speaker and current_text:
        segments.append({
            'speaker': current_speaker,
            'text': ' '.join(current_text).strip()
        })
    
    return segments

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
        "max_tokens": 3000
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content']
        
    except requests.RequestException as e:
        logger.error(f"❌ OpenRouter API error: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        raise

def generate_audio_google_cloud(segments: List[Dict], output_file: str) -> bool:
    """Generera audio med Google Cloud TTS"""
    try:
        # Importera Google Cloud TTS-modulen
        from google_cloud_tts import GoogleCloudTTS
        
        # Konvertera segments till rätt format för Google Cloud TTS
        audio_segments = []
        for i, segment in enumerate(segments):
            speaker = segment['speaker'].lower()
            
            # Mappa talare till röster
            if 'lisa' in speaker or 'sanna' in speaker:
                voice = 'lisa'
            elif 'pelle' in speaker or 'george' in speaker:
                voice = 'pelle'
            else:
                # Alternerande röster om talare inte är tydlig
                voice = 'lisa' if i % 2 == 0 else 'pelle'
            
            audio_segments.append({
                'voice': voice,
                'text': segment['text']
            })
        
        # Skapa TTS-instans och generera audio
        tts = GoogleCloudTTS()
        audio_file = tts.generate_podcast_audio(audio_segments)
        
        if audio_file and os.path.exists(audio_file):
            # Kopiera till önskad output-fil
            import shutil
            shutil.move(audio_file, output_file)
            logger.info(f"Audio genererad med Google Cloud TTS: {output_file}")
            return True
        else:
            logger.error("Google Cloud TTS-generering misslyckades")
            return False
            
    except ImportError as e:
        logger.error(f"google_cloud_tts.py import error: {e}")
        return False
    except Exception as e:
        logger.error(f"Fel vid audio-generering: {e}")
        return False

def generate_github_rss(episodes_data: List[Dict], base_url: str) -> str:
    """Generera RSS-feed för GitHub Pages"""
    rss_items = []
    
    for episode in episodes_data:
        pub_date = datetime.strptime(episode['date'], '%Y-%m-%d').strftime('%a, %d %b %Y %H:%M:%S +0000')
        
        rss_items.append(f"""
        <item>
            <title>{episode['title']}</title>
            <description>{episode['description']}</description>
            <pubDate>{pub_date}</pubDate>
            <enclosure url="{base_url}/audio/{episode['filename']}" length="{episode.get('size', 0)}" type="audio/mpeg"/>
            <guid>{base_url}/audio/{episode['filename']}</guid>
        </item>""")
    
    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
    <channel>
        <title>MMM Veckonytt - MÄNNISKA MASKIN MILJÖ</title>
        <description>En automatiskt genererad podcast med veckans viktigaste nyheter inom AI, teknik och klimat</description>
        <link>{base_url}</link>
        <language>sv-SE</language>
        <itunes:category text="Technology"/>
        <itunes:category text="Science"/>
        <itunes:explicit>false</itunes:explicit>
        <itunes:author>Pontus Dahlberg</itunes:author>
        <itunes:summary>Automatiserad podcast med AI-genererat innehåll om teknik, AI och klimat</itunes:summary>
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
    """Huvudfunktion för podcast-generering"""
    logger.info("[PODCAST] Startar MMM podcast-generering (GitHub-version)...")
    
    try:
            # Ladda konfiguration
            config = load_config()
            if not config:
                logger.error("[ERROR] Kunde inte ladda konfiguration")
                return False
            
            # Generera datum och filnamn
            today = datetime.now()
            date_str = today.strftime('%Y%m%d')
            timestamp = today.strftime('%Y%m%d_%H%M%S')
            
            # Skapa output-mapp om den inte finns
            os.makedirs('audio', exist_ok=True)
            os.makedirs('public/audio', exist_ok=True)
            
            # Mock podcast content för test (senare kan detta komma från scraper.py)
            podcast_content = """Lisa: Hej och välkommen till MMM - Människa Maskin Miljö! Jag heter Lisa.

Pelle: Och jag heter Pelle. Idag ska vi prata om de senaste nyheterna inom AI och teknik.

Lisa: Precis! Vi börjar med att OpenAI lanserat sin nya modell GPT-4 Turbo som är både snabbare och billigare än tidigare versioner.

Pelle: Det är verkligen spännande utveckling. Modellen kan hantera längre texter och ger mer precisa svar, vilket kommer att påverka många branscher.

Lisa: Ja, och inom klimatteknologi ser vi också stora framsteg. Tesla har presenterat sin nya batteriteknologi som kan lagra energi mer effektivt.

Pelle: Det här kan vara avgörande för övergången till förnybar energi. Bättre batterier betyder att vi kan använda sol- och vindkraft även när det inte blåser eller skiner.

Lisa: Exakt! Tack för att ni lyssnade på dagens avsnitt av MMM.

Pelle: Vi hörs imorgon med mer teknik och klimatnyheter. Ha det bra!"""
            
            # Parsa innehållet i segment
            segments = parse_podcast_text(podcast_content)
            logger.info(f"[PARSE] Hittade {len(segments)} segment att generera audio för")
            
            # Generera filnamn
            audio_filename = f"MMM_github_{timestamp}.mp3"
            audio_filepath = os.path.join('audio', audio_filename)
            
            # Generera audio med Google Cloud TTS
            logger.info("[TTS] Genererar audio med Google Cloud TTS...")
            success = generate_audio_google_cloud(segments, audio_filepath)
            
            if not success:
                logger.error("[ERROR] Audio-generering misslyckades")
                return False
            
            # Kopiera till public/audio för GitHub Pages
            public_audio_path = os.path.join('public', 'audio', audio_filename)
            shutil.copy2(audio_filepath, public_audio_path)
            logger.info(f"[FILES] Kopierade audio till {public_audio_path}")
            
            # Skapa episode data
            file_size = os.path.getsize(audio_filepath)
            episode_data = {
                'title': f"MMM Veckonytt - {today.strftime('%Y-%m-%d')}",
                'description': "Dagens nyheter inom AI, teknik och klimat",
                'date': today.strftime('%Y-%m-%d'),
                'filename': audio_filename,
                'size': file_size,
                'duration': "3:00"  # Ungefärlig längd
            }
            
            # Generera RSS-feed
            base_url = "https://pontusdahlberg.github.io/morgonpodden"
            rss_content = generate_github_rss([episode_data], base_url)
            
            # Spara RSS-feed till public/
            rss_path = os.path.join('public', 'feed.xml')
            with open(rss_path, 'w', encoding='utf-8') as f:
                f.write(rss_content)
            logger.info(f"[RSS] RSS-feed sparad till {rss_path}")
            
            # Logga framgång
            logger.info("[SUCCESS] Podcast-generering slutförd!")
            logger.info(f"[AUDIO] Audio: {audio_filepath}")
            logger.info(f"[RSS] RSS: {rss_path}")
            logger.info(f"[GITHUB] GitHub Pages URL: {base_url}")
            logger.info(f"[FEED] RSS URL: {base_url}/feed.xml")        return True
        
    except Exception as e:
        logger.error(f"❌ Oväntat fel: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)