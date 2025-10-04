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
    """Hämta aktuell väderdata för svenska landskap"""
    try:
        # Svenska landskap med representativa städer
        regions = [
            ("Götaland", "Goteborg"),   # Göteborg representerar Götaland
            ("Svealand", "Stockholm"),  # Stockholm representerar Svealand  
            ("Norrland", "Umea")        # Umeå representerar Norrland
        ]
        
        def convert_wind_speed(wind_text):
            """Konvertera vindstyrka från km/h till svenska termer"""
            import re
            # Hitta siffror i vindtexten
            wind_match = re.search(r'(\d+)km', wind_text)
            if wind_match:
                kmh = int(wind_match.group(1))
                # Konvertera km/h till m/s och sedan till svenska termer
                ms = kmh / 3.6
                if ms < 3:
                    return "svaga vindar"
                elif ms < 8:
                    return "måttliga vindar"
                elif ms < 14:
                    return "friska vindar"
                else:
                    return "hårda vindar"
            return "svaga vindar"
        
        weather_data = []
        for region_name, api_name in regions:
            try:
                # Använd wttr.in API för väderdata
                url = f"https://wttr.in/{api_name}?format=%C+%t+↑%w"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    weather_info = response.text.strip()
                    # Konvertera vindstyrka
                    wind_desc = convert_wind_speed(weather_info)
                    # Ta bort vindstyrka från weather_info och lägg till svensk term
                    import re
                    clean_weather = re.sub(r'↑\d+km.*', '', weather_info).strip()
                    weather_data.append(f"{region_name}: {clean_weather}, {wind_desc}")
                    
            except Exception as e:
                logger.warning(f"Kunde inte hämta väder för {region_name}: {e}")
                continue
        
        if weather_data:
            weather_text = f"Vädret idag: {', '.join(weather_data[:2])}"  # Bara två första för kompakthet
            logger.info(f"[WEATHER] {weather_text}")
            return weather_text
        else:
            return "Vädret idag: Varierande väderförhållanden över Sverige"
            
    except Exception as e:
        logger.error(f"[WEATHER] Fel vid väder-hämtning: {e}")
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

OUTRO-KRAV (MYCKET VIKTIGT):
- INGEN teasing av "nästa avsnitt" 
- INGA påhittade lyssnarfrågor
- STARK koppling till huvudpodden "Människa Maskin Miljö"
- Förklara att MMM Senaste Nytt är en del av Människa Maskin Miljö-familjen
- Uppmana lyssnare att kolla in huvudpodden för djupare analyser

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
                    segments.append({
                        'speaker': current_speaker,
                        'text': clean_text
                    })
            
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
            segments.append({
                'speaker': current_speaker,
                'text': clean_text
            })
    
    return segments

def generate_audio_google_cloud(segments: List[Dict], output_file: str) -> bool:
    """Generera audio med Google Cloud TTS"""
    try:
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
        
        # Använd alla tillgängliga musik från audio/music/ i rotation
        music_files = [
            "audio/music/MMM Senaste Nytt Från Människa Maskin Mi.mp3",
            "audio/music/Mellan Dröm och Verklighet.mp3", 
            "audio/music/Stjärnljus.mp3",
            "audio/music/The Moon and the Meadow.mp3"
        ]
        
        # Filtrera till endast existerande filer
        available_music = [f for f in music_files if os.path.exists(f)]
        
        if not available_music:
            logger.warning("[MUSIC] Inga musikfiler hittades")
            return audio_file
            
        # Välj slumpmässig låt för variation
        import random
        background_music = random.choice(available_music)
        logger.info(f"[MUSIC] Valde låt: {os.path.basename(background_music)}")
        
        if not background_music:
            logger.warning("[MUSIC] Ingen musik hittades, använder original")
            return audio_file
        
        # Generera musikversionen
        music_output = audio_file.replace('.mp3', '_with_music.mp3')
        
        # Mixa tal med bakgrundsmusik
        success = mixer.mix_speech_with_music(
            speech_file=audio_file,
            music_file=background_music,
            output_file=music_output,
            music_volume=-15,  # Låg volym i dB
            fade_in=2000,     # 2 sekunder fade-in
            fade_out=2000     # 2 sekunder fade-out
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
        
        # Generera audio med Google Cloud TTS
        logger.info("[TTS] Genererar audio med Google Cloud TTS...")
        success = generate_audio_google_cloud(segments, audio_filepath)
        
        if not success:
            logger.error("[ERROR] Audio-generering misslyckades")
            return False
        
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
            'description': f"Dagens nyheter inom AI, teknik och klimat - {today.strftime('%A den %d %B %Y')}. {weather_info}",
            'date': today.strftime('%Y-%m-%d'),
            'filename': audio_filename,
            'size': file_size,
            'duration': f"{estimated_minutes:.0f}:00"
        }
        
        # Generera RSS-feed
        base_url = "https://pontusdahlberg.github.io/morgonpodden"
        rss_content = generate_github_rss([episode_data], base_url)
        
        # Spara RSS-feed
        rss_path = os.path.join('public', 'feed.xml')
        with open(rss_path, 'w', encoding='utf-8') as f:
            f.write(rss_content)
        logger.info(f"[RSS] RSS-feed sparad: {rss_path}")
        
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