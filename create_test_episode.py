#!/usr/bin/env python3
"""
Förenklad podcast-generator för MMM Senaste Nytt
Fokus på att nå 10-minuters längd
"""

import os
import json
import logging
import feedparser
import requests
from datetime import datetime
from dotenv import load_dotenv
from google.cloud import texttospeech

load_dotenv()

# Sätt upp Google Cloud credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-service-account.json'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_news_articles(max_articles=50):
    """Hämta nyhetsartiklar från källor"""
    
    print("📰 Hämtar nyheter från källor...")
    
    with open('sources.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    sources = config.get('sources', [])
    articles = []
    
    for source in sources[:10]:  # Begränsa till första 10 källor för snabbhet
        if not source.get('enabled', True):
            continue
        
        try:
            print(f"  🔍 {source['name']}...")
            feed = feedparser.parse(source['url'])
            
            for entry in feed.entries[:source.get('maxItems', 5)]:
                article = {
                    'title': entry.title,
                    'description': getattr(entry, 'description', ''),
                    'source': source['name'],
                    'category': source.get('category', 'news'),
                    'url': getattr(entry, 'link', ''),
                    'published': getattr(entry, 'published', '')
                }
                articles.append(article)
                
                if len(articles) >= max_articles:
                    break
            
        except Exception as e:
            print(f"    ❌ Fel med {source['name']}: {e}")
            continue
    
    print(f"✅ Hämtade {len(articles)} artiklar totalt")
    return articles

def create_detailed_podcast_script(articles):
    """Skapa ett detaljerat podcastmanus med målsättning 10 minuter"""
    
    print("🤖 Genererar detaljerat podcastmanus...")
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    
    # Välj de mest intressanta artiklarna
    selected_articles = articles[:15]  # Ta fler artiklar för mer innehåll
    
    # Skapa sammanfattning av artiklar för prompten
    articles_summary = "\n\n".join([
        f"ARTIKEL {i+1}:\nTitel: {article['title']}\nKälla: {article['source']}\nBeskrivning: {article['description'][:200]}..."
        for i, article in enumerate(selected_articles)
    ])
    
    prompt = f"""Du skapar ett detaljerat 10-minuters podcastsamtal mellan Lisa och Pelle för "MMM Senaste Nytt".

Lisa: Expert inom hållbar teknik och AI, entusiastisk och engagerad
Pelle: AI-specialist med fokus på miljölösningar, analytisk men tillgänglig

VIKTIGT FÖR LÄNGD: Skapa ett samtal som är EXAKT 10 minuter (cirka 4000-5000 ord). Måste vara tillräckligt långt!

ARTIKLAR ATT DISKUTERA:
{articles_summary}

KRAV FÖR 10-MINUTERS LÄNGD:

1. DJUPGÅENDE DISKUSSION (inte bara snabba omnämnanden):
   - Varje artikel diskuteras i minst 1-2 minuter
   - Lisa och Pelle ställer följdfrågor till varandra
   - Praktiska exempel och verkliga konsekvenser
   - Personliga reflektioner och expertkommentarer

2. INTERAKTIV DIALOG:
   - "Vad tycker du om det här, Pelle?"
   - "Lisa, kan du förklara hur det fungerar?"
   - "Det påminner mig om..."
   - Naturliga övergångar och reaktioner

3. UTFÖRLIGA FÖRKLARINGAR:
   - Tekniska begrepp förklaras för lyssnare
   - Historisk bakgrund där relevant
   - Framtidsperspektiv och prognoser
   - Svenska perspektiv på internationella nyheter

4. OMFATTANDE INNEHÅLL:
   - 8-12 olika nyhetsämnen behandlas
   - Varje ämne får tillräckligt utrymme
   - Naturliga pauser och sammanfattningar
   - Avslutande reflektion över dagens teman

FORMAT: Skriv som ren dialog:

LISA: [första mening]
PELLE: [svar och fördjupning]
LISA: [följdfråga eller ny vinkel]
PELLE: [fortsatt diskussion]
...

VIKTIGT: Om dialogen blir kortare än 4000 ord, lägg till:
- Mer detaljerade diskussioner
- Fler följdfrågor mellan värdarna
- Utbyggda förklaringar av teknisk bakgrund
- Mer personliga reflektioner och kommentarer

Skapa nu ett omfattande 10-minuters samtal!"""

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'anthropic/claude-3-haiku',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 6000  # Mer tokens för längre innehåll
    }
    
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            script = result['choices'][0]['message']['content']
            
            # Analysera längd
            word_count = len(script.split())
            estimated_minutes = word_count / 150  # 150 ord per minut
            
            print(f"✅ Genererat manus: {word_count} ord")
            print(f"⏱️ Uppskattad längd: {estimated_minutes:.1f} minuter")
            
            # Spara manus
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            script_filename = f"scripts/generated_episode_{timestamp}.txt"
            
            os.makedirs('scripts', exist_ok=True)
            with open(script_filename, 'w', encoding='utf-8') as f:
                f.write(script)
            
            print(f"📁 Sparat som: {script_filename}")
            
            return script, word_count, estimated_minutes
            
        else:
            print(f"❌ AI-generering fel: {response.status_code} - {response.text}")
            return None, 0, 0
            
    except Exception as e:
        print(f"❌ Fel vid scriptgenerering: {e}")
        return None, 0, 0

def parse_script_to_segments(script):
    """Dela upp script i Lisa/Pelle-segment"""
    
    lines = script.strip().split('\n')
    segments = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Hantera både stora och små bokstäver
        if line.startswith('LISA:') or line.startswith('Lisa:'):
            text = line[5:].strip()
            if text:
                segments.append(('Lisa', text))
        elif line.startswith('PELLE:') or line.startswith('Pelle:'):
            text = line[6:].strip()
            if text:
                segments.append(('Pelle', text))
    
    print(f"🎭 Delat upp i {len(segments)} segment")
    return segments

def generate_tts_audio(segments):
    """Generera TTS-ljud med Chirp3-HD röster"""
    
    print("🎤 Genererar TTS-ljud...")
    
    client = texttospeech.TextToSpeechClient()
    
    # Röstdefinitioner
    voices = {
        'Lisa': texttospeech.VoiceSelectionParams(
            language_code="sv-SE",
            name="sv-SE-Chirp3-HD-Gacrux",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        ),
        'Pelle': texttospeech.VoiceSelectionParams(
            language_code="sv-SE", 
            name="sv-SE-Chirp3-HD-Charon",
            ssml_gender=texttospeech.SsmlVoiceGender.MALE
        )
    }
    
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    
    audio_files = []
    total_cost = 0
    
    for i, (speaker, text) in enumerate(segments):
        print(f"  🎙️ Segment {i+1}/{len(segments)}: {speaker} ({len(text)} tecken)")
        
        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voices[speaker],
                audio_config=audio_config
            )
            
            # Spara segment
            filename = f"episode_segment_{i+1:02d}_{speaker.lower()}.mp3"
            filepath = f"audio/{filename}"
            
            with open(filepath, "wb") as out:
                out.write(response.audio_content)
            
            audio_files.append(filepath)
            
            # Kostnad (Chirp3-HD)
            cost = len(text) * 0.000004
            total_cost += cost
            
        except Exception as e:
            print(f"    ❌ Fel med segment {i+1}: {e}")
    
    print(f"✅ Genererat {len(audio_files)} ljudfiler")
    print(f"💰 Total kostnad: ${total_cost:.4f}")
    
    return audio_files, total_cost

def create_full_episode():
    """Skapa ett komplett avsnitt"""
    
    print("🎙️ SKAPAR FULLSTÄNDIGT AVSNITT AV MMM SENASTE NYTT")
    print("="*60)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Starttid: {timestamp}")
    
    # 1. Hämta nyheter
    articles = fetch_news_articles(max_articles=50)
    
    if not articles:
        print("❌ Inga artiklar hämtades")
        return
    
    # 2. Generera detaljerat manus
    script, word_count, estimated_minutes = create_detailed_podcast_script(articles)
    
    if not script:
        print("❌ Kunde inte generera manus")
        return
    
    if estimated_minutes < 8:
        print("⚠️ VARNING: Manus för kort för 10-minuters mål!")
        print("💡 Överväg att lägga till fler artiklar eller mer detaljerad diskussion")
    
    # 3. Dela upp i segment
    segments = parse_script_to_segments(script)
    
    if not segments:
        print("❌ Kunde inte dela upp manus i segment")
        return
    
    # 4. Generera TTS
    audio_files, total_cost = generate_tts_audio(segments)
    
    # 5. Sammanfattning
    print(f"\n🎉 AVSNITT KLART!")
    print(f"📊 Statistik:")
    print(f"   • Artiklar: {len(articles)}")
    print(f"   • Ord i manus: {word_count}")
    print(f"   • Uppskattad längd: {estimated_minutes:.1f} minuter")
    print(f"   • Audio-segment: {len(audio_files)}")
    print(f"   • Kostnad: ${total_cost:.4f}")
    print(f"\n📁 Filer:")
    print(f"   • Manus: scripts/generated_episode_*.txt")
    print(f"   • Audio: audio/episode_segment_*.mp3")
    
    print(f"\n💡 Nästa steg:")
    print(f"   1. Lyssna på audio-filerna för kvalitetskontroll")
    print(f"   2. Lägg ihop i Audacity med musik")
    print(f"   3. Testa upload till Cloudflare om nöjd")

if __name__ == "__main__":
    create_full_episode()