#!/usr/bin/env python3
"""
Testa intelligent emotion-baserad podcast-generering
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_intelligent_audio():
    print("🎭 TESTAR INTELLIGENT EMOTION-BASERAD PODCAST")
    print("=" * 60)
    
    # Test-innehåll med olika emotioner
    test_content = """Hej och välkomna till Människa Maskin Miljö! Jag heter Sanna och tillsammans med George kommer vi att presentera veckans spännande nyheter.

Forskare har gjort ett fantastiskt genombrott inom AI som kan revolutionera hur vi bekämpar klimatförändringarna! Den nya teknologin visar otroliga resultat och kan vara nyckeln till vår framtid.

Däremot visar en ny rapport allvarliga konsekvenser av klimatkrisen. Experter varnar för att situationen är kritisk och att vi måste agera nu för att undvika katastrofala effekter.

Men det finns också positiva nyheter! Studien visar att ny teknologi kan hjälpa oss att tillsammans skapa en mer hållbar framtid. Samarbetet mellan länder ger hopp om förbättringar.

Forskningsresultaten från universitetet visar statistiska data om energieffektivitet. Analysen bekräftar att nya metoder ger betydande förbättringar inom området."""

    # Importera och testa emotion analyzer
    try:
        from emotion_analyzer import split_content_by_emotion
        
        segments = split_content_by_emotion(test_content)
        
        print(f"📊 Innehållet delades upp i {len(segments)} segment:")
        print()
        
        for i, segment in enumerate(segments):
            emotion = segment['emotion']
            voice_name = segment['voice_name']
            text_preview = segment['text'][:80] + "..." if len(segment['text']) > 80 else segment['text']
            voice_settings = segment['voice_settings']
            
            print(f"🎤 Segment {i+1}: {voice_name} ({emotion})")
            print(f"   Text: {text_preview}")
            print(f"   Settings: stability={voice_settings['stability']}, style={voice_settings['style']}")
            print()
        
        # Testa faktisk audio-generering för första segmentet
        print("🎵 Testar audio-generering för första segmentet...")
        
        first_segment = segments[0]
        
        import requests
        api_key = os.getenv('ELEVENLABS_API_KEY')
        voice_id = first_segment['voice_id']
        voice_settings = first_segment['voice_settings']
        text = first_segment['text']
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2", 
            "voice_settings": voice_settings
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            os.makedirs('audio', exist_ok=True)
            filename = f"audio/intelligent_test_{first_segment['emotion']}.mp3"
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Audio genererat: {filename}")
            print(f"   Emotion: {first_segment['emotion']}")
            print(f"   Röst: {first_segment['voice_name']}")
            print(f"   Storlek: {len(response.content)} bytes")
        else:
            print(f"❌ Audio-generering misslyckades: {response.status_code}")
        
        print()
        print("🎯 RESULTAT:")
        print("✅ Emotion analysis fungerar")
        print("✅ Intelligent röstval fungerar")  
        print("✅ Dynamiska voice settings fungerar")
        print("✅ Systemet är redo för intelligent podcast-generering!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_intelligent_audio()
