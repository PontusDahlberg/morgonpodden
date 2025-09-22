#!/usr/bin/env python3
"""
Testa Sanna med emotional style tags
"""
import requests
import os

def test_sanna_with_style():
    print("🎭 Testar Sanna med olika emotional styles")
    print("=" * 50)
    
    api_key = "sk_a52d33c85c9751b9cb8ca3e8671dff718f67a488ca50df30"
    voice_id = "4xkUqaR9MYOJHoaC1Nak"  # Sanna
    
    # Test olika styles
    tests = [
        {
            "style": "excited", 
            "text": "Hej och välkomna till Människa Maskin Miljö! Idag har vi otroliga AI-nyheter som verkligen kommer förändra framtiden!"
        },
        {
            "style": "newscast", 
            "text": "God morgon. Här är veckans viktigaste nyheter inom artificiell intelligens och klimatteknologi."
        },
        {
            "style": "friendly",
            "text": "Hej allihopa! Vad kul att ni lyssnar på Människa Maskin Miljö. Jag heter Sanna och idag ska vi prata om spännande utvecklingar."
        }
    ]
    
    for i, test in enumerate(tests):
        style = test["style"]
        text = test["text"]
        
        print(f"\n🎭 Test {i+1}: Style '{style}'")
        print(f"Text: {text[:50]}...")
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,  # Högre för bättre röstlikhet
                "style": style,            # ⭐ EMOTIONAL TAGGING!
                "use_speaker_boost": True  # Extra boost
            }
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                filename = f"audio/sanna_style_{style}.mp3"
                os.makedirs("audio", exist_ok=True)
                
                with open(filename, "wb") as f:
                    f.write(response.content)
                
                file_size = len(response.content)
                print(f"✅ Success! Sparad: {filename} ({file_size} bytes)")
            else:
                print(f"❌ Fel: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎧 Lyssna på filerna för att jämföra:")
    print("- audio/sanna_style_excited.mp3")
    print("- audio/sanna_style_newscast.mp3") 
    print("- audio/sanna_style_friendly.mp3")

if __name__ == "__main__":
    test_sanna_with_style()
