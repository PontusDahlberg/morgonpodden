#!/usr/bin/env python3
import requests
import os

def test_voice(voice_id, voice_name, accent, test_text):
    print(f"🎵 Testar {voice_name} ({accent}) - ID: {voice_id}")
    
    api_key = "sk_a52d33c85c9751b9cb8ca3e8671dff718f67a488ca50df30"
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
            filename = f"audio/test_{voice_name.lower()}.mp3"
            os.makedirs("audio", exist_ok=True)
            
            with open(filename, "wb") as f:
                f.write(response.content)
            
            file_size = len(response.content)
            print(f"✅ {voice_name} fungerar! Audio: {filename} ({file_size} bytes)")
            return True
        else:
            print(f"❌ {voice_name} misslyckades: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Fel vid test av {voice_name}: {e}")
        return False

# Test text
test_text = "Hej och välkomna till Människa Maskin Miljö! Tillsammans med Sanna kommer jag att presentera veckans viktigaste nyheter inom artificiell intelligens och klimatförändringar."

print("🎤 Testar tre amerikanska manliga röster")
print("=" * 50)

# Test alla tre röster
voices_to_test = [
    ("GBv7mTt0atIp3Br8iCZE", "Thomas", "amerikansk"),
    ("TX3LPaxmHKxFdv7VOQHJ", "Liam", "amerikansk"), 
    ("bIHbv24MWmeRgasZH58o", "Will", "amerikansk")
]

results = []
for voice_id, name, accent in voices_to_test:
    success = test_voice(voice_id, name, accent, test_text)
    results.append((name, success))
    print()

print("=" * 50)
print("📊 Sammanfattning av alla testade röster:")
print()
print("Kvinnlig värd:")
print("✅ Sanna (svensk professionell)")
print()
print("Manliga värdkandidater:")
print("✅ George (brittisk professionell)")
print("✅ Daniel (brittisk professionell)")
for name, success in results:
    status = "✅" if success else "❌"
    print(f"{status} {name} (amerikansk professionell)")

print()
print("🎧 Lyssna på alla ljudfiler i audio/ mappen för att välja!")
