#!/usr/bin/env python3
"""
Test script för att testa båda ElevenLabs röster
"""

import requests
import os
from dotenv import load_dotenv

def test_voice(voice_id, voice_name, test_text):
    """Testa en specifik röst"""
    print(f"\n🎵 Testar {voice_name} (ID: {voice_id})...")
    
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("❌ Ingen ElevenLabs API key hittades")
        return False
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    data = {
        "text": test_text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            # Spara testfil
            filename = f"audio/test_{voice_name.lower().replace(' ', '_')}.mp3"
            os.makedirs('audio', exist_ok=True)
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content)
            print(f"✅ {voice_name} fungerar! Audio sparad: {filename} ({file_size} bytes)")
            return True
        else:
            print(f"❌ {voice_name} misslyckades: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Fel vid test av {voice_name}: {e}")
        return False

def main():
    """Huvudfunktion för rösttest"""
    load_dotenv()
    
    print("🎤 Testar ElevenLabs röster för Människa Maskin Miljö")
    print("=" * 50)
    
    # Test text på svenska
    test_text = "Hej och välkomna till Människa Maskin Miljö! Dagens program handlar om artificiell intelligens och klimatförändringar."
    
    # Hämta röst-ID från miljövariabler
    female_voice_id = os.getenv('ELEVENLABS_VOICE_ID_FEMALE')
    male_voice_id = os.getenv('ELEVENLABS_VOICE_ID_MALE')
    
    if not female_voice_id:
        print("❌ ELEVENLABS_VOICE_ID_FEMALE saknas i .env")
        return
    
    if not male_voice_id:
        print("❌ ELEVENLABS_VOICE_ID_MALE saknas i .env")
        return
    
    # Testa båda rösterna
    female_success = test_voice(female_voice_id, "Sanna (Kvinnlig värd)", test_text)
    male_success = test_voice(male_voice_id, "George (Manlig värd)", test_text)
    
    print("\n" + "=" * 50)
    print("📊 Testresultat:")
    print(f"Kvinnlig röst (Sanna): {'✅ Fungerar' if female_success else '❌ Misslyckades'}")
    print(f"Manlig röst (George): {'✅ Fungerar' if male_success else '❌ Misslyckades'}")
    
    if female_success and male_success:
        print("\n🎉 Båda rösterna fungerar perfekt!")
        print("Du kan nu uppdatera GitHub Secrets och köra full podcast-generering.")
    else:
        print("\n⚠️ En eller båda rösterna misslyckades. Kontrollera API-nyckeln och röst-ID:n.")

if __name__ == "__main__":
    main()
