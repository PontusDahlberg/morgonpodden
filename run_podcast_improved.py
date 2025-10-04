#!/usr/bin/env python3
"""
Förbättrad podcast-generator för MMM Senaste Nytt
10-minuters daglig nyhetspodcast med struktur och diskussion
"""

import os
import sys
import json
import logging
import shutil
import requests
from datetime import datetime, timedelta
from typing import Dict, List
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

def generate_structured_podcast_content() -> str:
    """Generera strukturerat podcast-innehåll med AI"""
    
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
LÄNGD: Absolut mål är 10 minuter (minst 1800-2200 ord för talat innehåll)
VÄRDAR: Lisa (kvinnlig, professionell men vänlig) och Pelle (manlig, nyfiken och engagerad)

DETALJERAD STRUKTUR:
1. INTRO & VÄLKOMST (90-120 sekunder) - Personlig hälsning, dagens datum, väderkommentar
2. INNEHÅLLSÖVERSIKT (60-90 sekunder) - Detaljerad genomgång av alla ämnen
3. HUVUDNYHETER (7-8 minuter) - 6-8 nyheter med djup analys och dialog
4. DJUP DISKUSSION/ANALYS (3-4 minuter) - Lisa och Pelle diskuterar trender och framtid
5. SAMMANFATTNING (60-90 sekunder) - Detaljerad recap av alla ämnen
6. OUTRO & MMM-KOPPLING (60-90 sekunder) - Stark koppling till huvudpodden "Människa Maskin Miljö"

INNEHÅLLSKRAV:
- Lisa säger "MMM Senaste Nytt" naturligt och professionellt (inte överdrivet)
- Minst 6 konkreta nyheter från svenska och internationella källor
- Varje nyhet ska vara minst 100-150 ord inklusive diskussion
- Lisa och Pelle ska ha naturliga konversationer med följdfrågor
- Inkludera siffror, fakta och konkreta exempel
- Nämn specifika företag, forskare eller organisationer
- Väv in hur nyheter påverkar vardagslivs och framtiden

DIALOGREGLER:
- Använd naturliga övergångar: "Det påminner mig om...", "Apropå det...", "Interessant nog..."
- Lisa och Pelle ska ibland avbryta varandra naturligt
- Inkludera korta pauser för eftertanke: "Hmm, det är en bra poäng..."
- Använd svenska uttryck och vardagligt språk
- Variera meningslängderna för naturligt flyt

FORMAT: Skriv ENDAST som ren dialog med "Talarnamn: Text" - INGEN markdown eller formatering!
FÖRBJUDET: **, ##, ---, ###, rubriker, markeringar - bara ren dialog!

EXEMPEL INTRO:
Lisa: Hej och välkommen till MMM Senaste Nytt! Jag heter Lisa.
Pelle: Och jag heter Pelle. Idag är det {swedish_weekday} den {today.strftime('%d')} {today.strftime('%B').lower()}, och här i Stockholm är det faktiskt ganska fint väder för att vara oktober.
Lisa: Ja, det är det verkligen! Men vi har mycket att prata om idag, för det händer otroligt mycket inom våra områden.
Pelle: Precis! Så vad har vi på agendan idag då?

SPECIELLA REGLER:
- INGEN "nästa avsnitt"-teasing eller förhandsvisning av framtida avsnitt
- INGA påhittade lyssnarfrågor eller fabricerat innehåll  
- STARK koppling till "Människa Maskin Miljö" i outro - berätta hur denna dagliga podcast kompletterar veckovisningarna
- Fokus på ÄKTA diskussion och reflektion mellan Lisa och Pelle

VIKTIGT: Endast dialog - inga rubriker eller formatering! Bara "Namn: Text" rad för rad.

Skapa nu ett KOMPLETT och LÅNGT manus för dagens avsnitt - kom ihåg att det ska vara minst 1800 ord:"""

    messages = [{"role": "user", "content": prompt}]
    
    try:
        content = get_openrouter_response(messages)
        logger.info("[AI] Genererade podcast-innehåll från AI")
        return content
    except Exception as e:
        logger.error(f"[ERROR] Kunde inte generera AI-innehåll: {e}")
        # Fallback till mock-innehåll
        return generate_fallback_content(date_str, swedish_weekday)

def generate_fallback_content(date_str: str, weekday: str) -> str:
    """Fallback-innehåll om AI inte fungerar"""
    return f"""Lisa: Hej och välkommen till MMM Senaste Nytt! Jag heter Lisa.

Pelle: Och jag heter Pelle. Idag är det {weekday} den {datetime.now().strftime('%d')} oktober, och vi har samlat dagens viktigaste nyheter inom teknik, AI och klimat.

Lisa: I dagens avsnitt ska vi prata om OpenAI:s senaste uppdatering av GPT-4, Teslas nya batteriteknologi, och de senaste klimatrapporterna från IPCC.

Pelle: Vi börjar med tekniknyheter. OpenAI har lanserat en förbättrad version av GPT-4 som de kallar GPT-4 Turbo. Modellen är inte bara snabbare, utan också betydligt billigare att använda för utvecklare.

Lisa: Det är verkligen stora nyheter, Pelle. Vad tror du det betyder för svenska företag som använder AI?

Pelle: Jag tror det kommer att demokratisera AI-användningen. Mindre företag kommer nu ha råd att bygga avancerade AI-lösningar. Vi kommer troligen se en våg av innovation inom allt från kundtjänst till kreativt arbete.

Lisa: Spännande! Vi fortsätter med klimatnyheter. Tesla har presenterat sina nya 4680-batterier som påstås ha 50% bättre energidensitet än tidigare generationer.

Pelle: Det där är riktigt intressanta nyheter. Bättre batterier är nyckeln till både elbilar och energilagring för sol- och vindkraft. Vad betyder det här för Sveriges klimatmål?

Lisa: Enligt Energimyndigheten kan den här typen av batteriteknologi påskynda vår övergång till förnybar energi med flera år. Vi kan faktiskt nå våra 2030-mål tidigare än planerat.

Pelle: Samtidigt har IPCC släppt en ny rapport som visar att vi fortfarande inte gör tillräckligt globalt. Temperaturen fortsätter att stiga snabbare än väntat.

Lisa: Det är en påminnelse om att teknik ensam inte räcker. Vi behöver också förändra våra beteenden och politiska system.

Pelle: Absolut. Men det finns hopp i de tekniska framstegen vi ser.

Lisa: Låt oss sammanfatta dagens avsnitt. Vi har pratat om OpenAI:s GPT-4 Turbo som gör AI mer tillgänglig, Teslas nya batterier som kan accelerera klimatomställningen, och IPCC:s påminnelse om att vi behöver agera snabbare.

Pelle: Vikten av att följa både teknisk innovation och klimatvetenskap blir tydlig. Det är precis det vi gör här på MMM Senaste Nytt - vi kopplar ihop människa, maskin och miljö.

Lisa: Precis! Och kom ihåg att det här är en del av det större programmet "Människa Maskin Miljö" där vi går djupare in på hur teknik, klimat och samhälle påverkar varandra.

Pelle: Tack för att ni lyssnade på dagens avsnitt! Vi hörs imorgon med fler nyheter från världen av teknik och klimat.

Lisa: Ha en bra dag och tänk på hur ni kan bidra till en mer hållbar framtid!"""

def clean_text_for_tts(text: str) -> str:
    """Ta bort markdown-formattering och andra tecken som inte ska läsas upp"""
    import re
    
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

def generate_audio_with_music(segments: List[Dict], output_file: str) -> bool:
    """Generera audio med Google Cloud TTS och musikbryggkor"""
    try:
        from google_cloud_tts import GoogleCloudTTS
        
        # Konvertera segments till rätt format för TTS
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
        
        # Skapa TTS-instans och generera grundläggande audio
        tts = GoogleCloudTTS()
        basic_audio_file = tts.generate_podcast_audio(audio_segments)
        
        if not basic_audio_file or not os.path.exists(basic_audio_file):
            logger.error("[ERROR] TTS-generering misslyckades")
            return False
        
        # Förbered segment-data för musik-mixer
        music_segments = []
        temp_dir = "temp_segments"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Dela upp audio i segment för musik-mixer
        from pydub import AudioSegment
        full_audio = AudioSegment.from_file(basic_audio_file)
        
        # Beräkna ungefärlig segment-längd baserat på text
        total_chars = sum(len(seg['text']) for seg in segments)
        segment_times = []
        current_time = 0
        
        for segment in segments:
            # Uppskatta tid baserat på textlängd (150 ord/minut ≈ 10 tecken/sekund)
            segment_duration = int((len(segment['text']) / 10) * 1000)  # millisekunder
            segment_times.append((current_time, current_time + segment_duration))
            current_time += segment_duration
        
        # Skapa individuella segment-filer för musik-mixer
        for i, ((start, end), segment) in enumerate(zip(segment_times, segments)):
            if end > len(full_audio):
                end = len(full_audio)
            if start < len(full_audio):
                segment_audio = full_audio[start:end]
                segment_file = os.path.join(temp_dir, f"segment_{i:02d}.mp3")
                segment_audio.export(segment_file, format="mp3")
                
                # Bestämma emotion baserat på innehåll
                text = segment['text'].lower()
                if any(word in text for word in ['spännande', 'fantastisk', 'otrolig', 'revolutioner']):
                    emotion = 'exciting'
                elif any(word in text for word in ['allvarlig', 'viktig', 'problem', 'klimat']):
                    emotion = 'serious'  
                elif any(word in text for word in ['hej', 'välkommen', 'tack', 'avslut']):
                    emotion = 'friendly'
                else:
                    emotion = 'professional'
                
                music_segments.append({
                    'speech_file': segment_file,
                    'emotion': emotion,
                    'duration': (end - start) // 1000
                })
        
        # Använd musik-mixer för att skapa final podcast med musikbryggkor
        mixer = MusicMixer()
        success = mixer.create_podcast_with_musical_bridges(music_segments, output_file)
        
        # Rensa temporära filer
        import shutil as sh
        if os.path.exists(temp_dir):
            sh.rmtree(temp_dir)
        if os.path.exists(basic_audio_file):
            os.remove(basic_audio_file)
        
        if success:
            logger.info(f"[MUSIC] Audio med musik genererad: {output_file}")
            return True
        else:
            # Fallback: bara kopiera grundläggande audio
            shutil.move(basic_audio_file, output_file)  
            logger.info(f"[TTS] Fallback audio utan musik: {output_file}")
            return True
            
    except Exception as e:
        logger.error(f"[ERROR] Audio-generering med musik misslyckades: {e}")
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
        <title>MMM Senaste Nytt - MÄNNISKA MASKIN MILJÖ</title>
        <description>Dagliga nyheter från världen av människa, maskin och miljö - med Lisa och Pelle</description>
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
            <itunes:email>pontusdahlberg@gmail.com</itunes:email>
        </itunes:owner>
        <itunes:image href="{base_url}/cover.jpg"/>
        <lastBuildDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}</lastBuildDate>
        {''.join(rss_items)}
    </channel>
</rss>"""
    
    return rss_content

def main():
    """Huvudfunktion för förbättrad podcast-generering"""
    logger.info("[PODCAST] Startar förbättrad MMM Senaste Nytt...")
    
    try:
        # Ladda konfiguration
        config = load_config()
        
        # Generera datum och filnamn
        today = datetime.now()
        timestamp = today.strftime('%Y%m%d_%H%M%S')
        
        # Skapa output-mappar
        os.makedirs('audio', exist_ok=True)
        os.makedirs('public/audio', exist_ok=True)
        
        # Generera strukturerat podcast-innehåll med AI
        logger.info("[AI] Genererar strukturerat podcast-innehåll...")
        podcast_content = generate_structured_podcast_content()
        
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
        
        # Generera audio med Google Cloud TTS och musik
        logger.info("[TTS+MUSIC] Genererar audio med TTS och musikbryggkor...")
        success = generate_audio_with_music(segments, audio_filepath)
        
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
            'title': f"MMM Senaste Nytt - {today.strftime('%d %B %Y')}",
            'description': f"Dagens nyheter inom AI, teknik och klimat - {today.strftime('%A den %d %B %Y')}",
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
        logger.info("[SUCCESS] Förbättrad podcast-generering slutförd!")
        logger.info(f"[AUDIO] Audio: {audio_filepath}")
        logger.info(f"[SCRIPT] Manus: {script_path}")
        logger.info(f"[RSS] RSS: {rss_path}")
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