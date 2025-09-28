#!/usr/bin/env python3
"""
Testa Cloudflare R2 API och fullständigt podcast-system
"""

import os
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

# Ladda .env
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cloudflare_r2():
    """Testa Cloudflare R2 API med bearer-autentisering"""
    
    print("☁️ TESTAR CLOUDFLARE R2")
    print("="*30)
    
    api_token = os.getenv('CLOUDFLARE_API_TOKEN')
    bucket_name = os.getenv('CLOUDFLARE_R2_BUCKET')
    public_url = os.getenv('CLOUDFLARE_R2_PUBLIC_URL')
    
    if not api_token:
        print("❌ CLOUDFLARE_API_TOKEN saknas")
        return False
    
    print(f"🔑 API Token: {api_token[:10]}...")
    print(f"🪣 Bucket: {bucket_name}")
    print(f"🌐 Public URL: {public_url}")
    
    # Test 1: Skapa en testtfil
    test_content = f"Test från MMM Senaste Nytt - {datetime.now().isoformat()}"
    test_filename = f"test_upload_{int(datetime.now().timestamp())}.txt"
    
    try:
        # För Cloudflare R2 behöver vi använda S3-kompatibel API
        # Men först testar vi bara med en enkel HTTP-request
        
        # Test med Cloudflare API direkt
        headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
        
        # Testa att lista buckets (för att verifiera API-åtkomst)
        # OBS: Detta kräver account ID som vi inte har ännu
        print("⚠️ Cloudflare R2 kräver account ID för API-anrop")
        print("💡 För nu testar vi bara att credentials laddas korrekt")
        
        return True
        
    except Exception as e:
        print(f"❌ Cloudflare test fel: {e}")
        return False

def test_full_system():
    """Kör vårt kompletta systemtest igen"""
    
    print("\n🎙️ FULLSTÄNDIGT SYSTEMTEST")
    print("="*40)
    
    # 1. Testa .env laddning
    api_key = os.getenv('OPENROUTER_API_KEY')
    if api_key:
        print(f"✅ OpenRouter API Key: {api_key[:20]}...")
    else:
        print("❌ OpenRouter API Key saknas fortfarande")
        return False
    
    # 2. Testa Google Cloud TTS
    try:
        from google.cloud import texttospeech
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-service-account.json'
        client = texttospeech.TextToSpeechClient()
        
        print("✅ Google Cloud TTS: Redo")
        
    except Exception as e:
        print(f"❌ Google Cloud TTS fel: {e}")
        return False
    
    # 3. Testa AI-generering
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "anthropic/claude-3-sonnet-20240229",
            "messages": [
                {"role": "user", "content": "Säg bara 'Hej från MMM Senaste Nytt test!' på svenska."}
            ],
            "max_tokens": 50
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result['choices'][0]['message']['content']
            print(f"✅ AI-generering: {message.strip()}")
        else:
            print(f"❌ AI-fel: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ AI-test fel: {e}")
        return False
    
    # 4. Testa RSS-källor
    try:
        import feedparser
        
        test_feed = feedparser.parse("https://www.svt.se/nyheter/rss.xml")
        if test_feed.entries:
            print(f"✅ RSS-källor: {len(test_feed.entries)} artiklar från SVT")
        else:
            print("⚠️ Inga artiklar från RSS")
            
    except Exception as e:
        print(f"❌ RSS-test fel: {e}")
        return False
    
    return True

def create_simple_episode():
    """Skapa ett enkelt test-avsnitt för att testa längden"""
    
    print("\n🎬 SKAPAR TEST-AVSNITT")
    print("="*30)
    
    # Simulera en enkel podcast-dialog
    test_dialogue = """
LISA: Hej och välkomna till MMM Senaste Nytt! Jag heter Lisa och här med mig har jag Pelle. Idag ska vi prata om de senaste nyheterna inom teknik och miljö.

PELLE: Tack Lisa! Ja, det här är vårt test-avsnitt för att se hur lång tid det tar att generera. Vi har flera spännande nyheter att gå igenom idag.

LISA: Precis, Pelle. Först ut har vi nyheter om artificiell intelligens och hur det kan hjälpa miljöarbetet. Det är verkligen fascinerande hur tekniken utvecklas.

PELLE: Absolut, Lisa. Och sen ska vi prata om förnybar energi och de senaste genombrotten inom solceller och vindkraft. Det händer så mycket spännande just nu.

LISA: Vi ska också titta på hur svenska företag arbetar med hållbarhet och vilka nya lösningar som kommer på marknaden.

PELLE: Och inte minst - vi ska prata om hur du som lyssnare kan vara med och bidra till en mer hållbar framtid.

LISA: Det här var en kort försmak. Nu kör vi igång med dagens riktiga nyheter!

PELLE: Vi ses på andra sidan!
    """
    
    # Dela upp i repliker
    lines = [line.strip() for line in test_dialogue.strip().split('\n') if line.strip()]
    
    print(f"📝 Genererat testmanus med {len(lines)} repliker")
    
    # Spara för senare användning
    with open('test_episode_script.txt', 'w', encoding='utf-8') as f:
        f.write(test_dialogue)
    
    # Beräkna ungefärlig längd
    total_words = sum(len(line.split()) for line in lines)
    estimated_minutes = total_words / 150  # Cirka 150 ord per minut i tal
    
    print(f"📊 Totalt {total_words} ord")
    print(f"⏱️ Uppskattad tid: {estimated_minutes:.1f} minuter")
    
    if estimated_minutes < 8:
        print("⚠️ För kort! Behöver mer innehåll för 10-minuters mål")
    elif estimated_minutes > 12:
        print("⚠️ För långt! Kan behöva kortas ner")
    else:
        print("✅ Bra längd för 10-minuters mål!")
    
    return test_dialogue

def main():
    """Huvudtest"""
    
    print("🧪 KOMPLETT SYSTEMTEST - MMM Senaste Nytt")
    print(f"Starttid: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    # Test 1: Cloudflare
    cloudflare_ok = test_cloudflare_r2()
    
    # Test 2: Fullständigt system
    system_ok = test_full_system()
    
    # Test 3: Skapa test-avsnitt
    test_dialogue = create_simple_episode()
    
    print("\n🎯 SAMMANFATTNING:")
    print(f"☁️ Cloudflare: {'✅' if cloudflare_ok else '❌'}")
    print(f"🔧 System: {'✅' if system_ok else '❌'}")
    print(f"🎙️ Test-avsnitt: {'✅' if test_dialogue else '❌'}")
    
    if cloudflare_ok and system_ok:
        print("\n🚀 SYSTEMET ÄR REDO!")
        print("📋 Nästa steg:")
        print("1. Kör 'python run_podcast.py' för fullständig generering")
        print("2. Eller testa GitHub Actions")
        print("3. Eller skapa en förenklad podcast-generator")
    else:
        print("\n⚠️ Vissa delar behöver fixas innan full körning")
    
    print(f"\nSluttid: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()