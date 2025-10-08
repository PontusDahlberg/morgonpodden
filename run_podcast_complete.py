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
from datetime import datetime, timedelta
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
            # Svenska landskap med representativa städer
            regions = [
                ("Götaland", "Goteborg"),
                ("Svealand", "Stockholm"),  
                ("Norrland", "Umea")
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
                weather_text = f"Vädret idag: {', '.join(weather_data[:2])}"
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

def generate_structured_podcast_content(weather_info: str) -> str:
    """Generera strukturerat podcast-innehåll med AI och riktig väderdata"""
    
    # Dagens datum för kontext
    today = datetime.now()
    date_str = today.strftime('%Y-%m-%d')
    weekday = today.strftime('%A')
    swedish_weekdays = {
        'Monday': 'måndag', 'Tuesday': 'tisdag', 'Wednesday': 'onsdag',
        'Thursday': 'torsdag', 'Friday': 'fredag', 'Saturday': 'lördag', 'Sunday': 'söndag'
    }
    swedish_weekday = swedish_weekdays.get(weekday, weekday)
    
    prompt = f"""Skapa ett KOMPLETT och DETALJERAT manus för dagens avsnitt av "MMM Senaste Nytt" - en svensk daglig nyhetspodcast om teknik, AI och klimat.

DATUM: {date_str} ({swedish_weekday})
VÄDER: {weather_info}
LÄNGD: Absolut mål är 10 minuter (minst 1800-2200 ord för talat innehåll)
VÄRDAR: Lisa (kvinnlig, professionell men vänlig) och Pelle (manlig, nyfiken och engagerad)

DETALJERAD STRUKTUR:
1. INTRO & VÄLKOMST (90-120 sekunder) - Inkludera RIKTIG väderinfo från "{weather_info}"
2. INNEHÅLLSÖVERSIKT (60-90 sekunder) - Detaljerad genomgång av alla ämnen
3. HUVUDNYHETER (6-7 minuter) - 5-6 nyheter med djup analys och dialog  
4. DJUP DISKUSSION/ANALYS (2-3 minuter) - Lisa och Pelle diskuterar trender och framtid
5. SAMMANFATTNING (60-90 sekunder) - Detaljerad recap av alla ämnen
6. OUTRO & MMM-KOPPLING (60-90 sekunder) - STARK koppling till huvudpodden "Människa Maskin Miljö"

INNEHÅLLSKRAV:
- Lisa säger "MMM Senaste Nytt" naturligt och professionellt (inte överdrivet)
- Använd RIKTIG väderdata: "{weather_info}" - inte påhittade kommentarer om "fin dag i Stockholm"
- Minst 6 konkreta nyheter från svenska och internationella källor
- Varje nyhet ska vara minst 150-200 ord inklusive diskussion
- Lisa och Pelle ska ha naturliga konversationer med följdfrågor
- Inkludera siffror, fakta och konkreta exempel
- Nämn specifika företag, forskare eller organisationer

KÄLLHÄNVISNING - MYCKET VIKTIGT:
- VARJE nyhet MÅSTE ha tydlig källhänvisning (t.ex. "enligt DN idag", "rapporterar SVT", "skriver Dagens Industri")
- Specifika personer MÅSTE namnges (t.ex. "Miljöminister Romina Pourmokhtari säger...", "Enligt statsminister Ulf kristersson...")
- Konkreta detaljer MÅSTE inkluderas (t.ex. "regeringen föreslår sänka utsläppen med 15% till 2030 genom att...")
- När möjligt: nämn specifika studier, rapporter eller undersökningar (t.ex. "enligt KTH:s nya studie", "Naturvårdsverkets rapport visar")
- För företagsnyheter: nämn pressmeddelanden, VD-uttalanden eller kvartalssiffror
- Om det är oklart VAD eller HUR - säg det tydligt ("detaljerna är ännu inte kända", "ingen tidsplan har presenterats")
- Undvik vaga termer som "regeringen har tagit initiativ" - var specifik om vad som faktiskt sagts eller beslutats
- Lyssnarna ska kunna förstå HUR nyheten blev känd och VARIFRÅN informationen kommer

OUTRO-KRAV (MYCKET VIKTIGT):
- INGEN teasing av "nästa avsnitt" 
- INGA påhittade lyssnarfrågor
- STARK koppling till huvudpodden "Människa Maskin Miljö"
- Förklara att MMM Senaste Nytt är en del av Människa Maskin Miljö-familjen
- Uppmana lyssnare att kolla in huvudpodden för djupare analyser
- OBLIGATORISK AI-BRASKLAPP: Lisa och Pelle ska ödmjukt förklara att de är aj-röster och att information kan innehålla fel, hänvisa till länkarna i avsnittsinformationen för verifiering

DIALOGREGLER:
- Använd naturliga övergångar: "Det påminner mig om...", "Apropå det...", "Interessant nog..."
- Lisa och Pelle ska ibland avbryta varandra naturligt
- Inkludera korta pauser för eftertanke: "Hmm, det är en bra poäng..."
- Använd svenska uttryck och vardagligt språk
- Variera meningslängderna för naturligt flyt

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
        return content
    except Exception as e:
        logger.error(f"[ERROR] Kunde inte generera AI-innehåll: {e}")
        # Fallback till mock-innehåll
        return generate_fallback_content(date_str, swedish_weekday, weather_info)

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
        
        rss_items.append(f"""        <item>
            <title>{episode['title']}</title>
            <description>{episode['description']}</description>
            <pubDate>{pub_date}</pubDate>
            <enclosure url="{audio_url}" length="{file_size}" type="audio/mpeg"/>
            <guid>{guid}</guid>
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
        podcast_content = generate_structured_podcast_content(weather_info)
        
        # Spara manus för referens
        script_path = f"podcast_script_{timestamp}.txt"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(podcast_content)
        logger.info(f"[SCRIPT] Manus sparat: {script_path}")
        
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
        
        # Skapa episode data
        file_size = os.path.getsize(audio_filepath)
        episode_data = {
            'title': f"MMM Senaste Nytt - {today.strftime('%d %B %Y')}",
            'description': f"Dagens nyheter inom AI, teknik och klimat - {today.strftime('%A den %d %B %Y')}. Med detaljerade källhänvisningar från svenska och internationella medier. {weather_info}",
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