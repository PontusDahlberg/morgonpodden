#!/usr/bin/env python3
import requests
import os

def test_kalle():
    print("🎤 Testar Kalle som ny manlig värd")
    print("=" * 40)
    
    voice_id = "xl55bIOowKkrStWvtatC"
    test_text = "Hej alla lyssnare! Jag heter Kalle och tillsammans med Sanna kommer jag att presentera veckans viktigaste nyheter inom AI och klimat."
    
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("❌ ELEVENLABS_API_KEY environment variable not found!")
        return
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
        print(f"🎵 Testar Kalle (ID: {voice_id})...")
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            filename = "audio/test_kalle.mp3"
            os.makedirs("audio", exist_ok=True)
            
            with open(filename, "wb") as f:
                f.write(response.content)
            
            file_size = len(response.content)
            print(f"✅ Kalle fungerar! Audio sparad: {filename} ({file_size} bytes)")
            
            print()
            print("📊 Testresultat:")
            print("Kalle (Manlig värd): ✅ Fungerar")
            print()
            print("🎉 Kalle fungerar utmärkt som manlig värd!")
            print("Nu har du Sanna + Kalle som värdpar för podden.")
            return True
        else:
            print(f"❌ Kalle misslyckades: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Fel vid test av Kalle: {e}")
        return False

if __name__ == "__main__":
    test_kalle()
