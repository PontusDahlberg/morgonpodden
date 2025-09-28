#!/usr/bin/env python3
"""
Enkel test av podcast-generering med vårt nya Google Cloud TTS system
"""

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Ladda .env först
load_dotenv()

# Sätt upp logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def simple_podcast_test():
    """Enkel test av podcast-systemet"""
    
    print("🎙️ ENKEL PODCAST-TEST")
    print("="*30)
    
    # 1. Testa Google Cloud TTS
    try:
        from google.cloud import texttospeech
        
        # Sätt credentials
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-service-account.json'
        
        client = texttospeech.TextToSpeechClient()
        
        # Test med kort text
        test_text = "Hej och välkomna till dagens test av MMM Senaste Nytt!"
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="sv-SE",
            name="sv-SE-Chirp3-HD-Gacrux",  # Lisa
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        synthesis_input = texttospeech.SynthesisInput(text=test_text)
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Spara test-audio
        with open("audio/tts_test.mp3", "wb") as out:
            out.write(response.audio_content)
        
        print("✅ Google Cloud TTS fungerar!")
        
    except Exception as e:
        print(f"❌ Google Cloud TTS fel: {e}")
        return False
    
    # 2. Testa att läsa källor
    try:
        with open('sources.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        sources = config.get('sources', [])
        active_sources = [s for s in sources if s.get('enabled', True)]
        
        print(f"📰 Hittade {len(active_sources)} aktiva källor")
        
        # Testa att hämta från en källa
        import feedparser
        
        test_source = active_sources[0] if active_sources else None
        if test_source:
            print(f"🔍 Testar källa: {test_source['name']}")
            
            try:
                feed = feedparser.parse(test_source['url'])
                if feed.entries:
                    print(f"✅ Hämtade {len(feed.entries)} artiklar från {test_source['name']}")
                    
                    # Visa första artikeln
                    first_entry = feed.entries[0]
                    print(f"📄 Exempel: {first_entry.title[:60]}...")
                else:
                    print(f"⚠️ Inga artiklar från {test_source['name']}")
                    
            except Exception as e:
                print(f"❌ Fel med källa {test_source['name']}: {e}")
        
    except Exception as e:
        print(f"❌ Källtest fel: {e}")
        return False
    
    # 3. Testa OpenRouter för AI-generering
    try:
        import requests
        
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            print("⚠️ OPENROUTER_API_KEY saknas")
            return False
        
        # Enkel test-prompt
        test_prompt = """Skapa en kort (2 minuter) podcast-dialog mellan Lisa och Pelle om dagens teknologi-nyheter. 

Lisa: Expert inom hållbar teknik
Pelle: AI-specialist

Format:
LISA: [första mening]
PELLE: [svar]
LISA: [uppföljning]
PELLE: [avslutning]

Ämne: Testa vårt nya podcastsystem."""

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "anthropic/claude-3-sonnet-20240229",
            "messages": [
                {"role": "user", "content": test_prompt}
            ],
            "max_tokens": 1000
        }
        
        print("🤖 Testar AI-generering...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            dialogue = result['choices'][0]['message']['content']
            
            print("✅ AI-generering fungerar!")
            print("\n📝 Genererat testsamtal:")
            print("-" * 40)
            print(dialogue[:300] + "..." if len(dialogue) > 300 else dialogue)
            print("-" * 40)
            
            # Spara för senare användning
            with open('test_dialogue.txt', 'w', encoding='utf-8') as f:
                f.write(dialogue)
            
        else:
            print(f"❌ AI-fel: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ AI-test fel: {e}")
        return False
    
    print("\n🎉 ALLA TESTER KLARADE!")
    print("✅ Google Cloud TTS: Fungerar")
    print("✅ RSS-källor: Fungerar")  
    print("✅ AI-generering: Fungerar")
    print("\n💡 Systemet är redo för fullständig podcast-generering!")
    
    return True

if __name__ == "__main__":
    print(f"🧪 System-test startad: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = simple_podcast_test()
    
    if success:
        print("\n🚀 NÄSTA STEG:")
        print("1. Kör 'python run_podcast.py' för fullständig generering")
        print("2. Eller skapa GitHub Actions test")
        print("3. Eller bygg en enkel podcast-generator")
    
    print(f"\nTest slutfört: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")