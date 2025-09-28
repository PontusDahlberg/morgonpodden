#!/usr/bin/env python3
"""
Test Chirp3-HD med helt ren text utan formatering-problem
"""

import os
from google.cloud import texttospeech

# Set up Google Cloud credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-service-account.json'

def test_clean_chirp3_hd():
    """Test Chirp3-HD med perfekt formaterad text"""
    
    client = texttospeech.TextToSpeechClient()
    
    # Helt ren text utan extra mellanslag eller indrag
    clean_text = "Hej och välkomna till vår morgonpodd! Idag ska vi prata om något verkligen spännande - vi har hittat en ny artist som kommer att förändra hela musikscenen. Men först... lite mer seriösa nyheter. Situationen i världen just nu kräver vår uppmärksamhet. Det här är verkligen viktigt att komma ihåg, alla lyssnare! Men nu tillbaka till den glada stämningen - vi avslutar med veckans bästa låt!"
    
    print("🎤 Testing Chirp3-HD med helt ren text...")
    print(f"Text: {clean_text}")
    print(f"Längd: {len(clean_text)} tecken")
    
    # Test med samma röst som innan
    voice = texttospeech.VoiceSelectionParams(
        language_code="sv-SE",
        name="sv-SE-Chirp3-HD-Aoede",  # Female voice 
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
    )
    
    try:
        synthesis_input = texttospeech.SynthesisInput(text=clean_text)
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Save clean version
        with open("audio/chirp3_hd_CLEAN_test.mp3", "wb") as out:
            out.write(response.audio_content)
        
        print("✅ Generated: audio/chirp3_hd_CLEAN_test.mp3")
        
        cost = len(clean_text) * 0.000004  # $4 per 1M chars
        print(f"💰 Cost: ${cost:.4f}")
        
        print("\n🔍 Debug info:")
        print(f"First 50 chars: '{clean_text[:50]}'")
        print(f"Any hidden chars: {repr(clean_text[:20])}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_different_chirp3_voices():
    """Testa några olika Chirp3-HD röster för att hitta bästa"""
    
    client = texttospeech.TextToSpeechClient()
    
    clean_text = "Hej och välkomna till vår morgonpodd! Idag ska vi prata om något verkligen spännande."
    
    # Testa några olika Chirp3-HD röster
    voices_to_test = [
        ("sv-SE-Chirp3-HD-Aoede", "FEMALE", "Aoede"),
        ("sv-SE-Chirp3-HD-Despina", "FEMALE", "Despina"), 
        ("sv-SE-Chirp3-HD-Gacrux", "FEMALE", "Gacrux"),
        ("sv-SE-Chirp3-HD-Charon", "MALE", "Charon"),
        ("sv-SE-Chirp3-HD-Puck", "MALE", "Puck"),
    ]
    
    print("\n🎭 Testing different Chirp3-HD voices...")
    
    for voice_name, gender, description in voices_to_test:
        print(f"\n🎤 Testing {description} ({gender})...")
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="sv-SE",
            name=voice_name,
            ssml_gender=texttospeech.SsmlVoiceGender[gender]
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
        )
        
        try:
            synthesis_input = texttospeech.SynthesisInput(text=clean_text)
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            filename = f"chirp3_voice_test_{description.lower()}.mp3"
            with open(f"audio/{filename}", "wb") as out:
                out.write(response.audio_content)
            
            print(f"✅ Generated: audio/{filename}")
            
        except Exception as e:
            print(f"❌ Error with {description}: {e}")

if __name__ == "__main__":
    # Test med helt ren text
    test_clean_chirp3_hd()
    
    # Test olika röster
    test_different_chirp3_voices()
    
    print("\n🎯 Nu kan du lyssna på:")
    print("• audio/chirp3_hd_CLEAN_test.mp3 - Ren text utan formatering-problem")
    print("• audio/chirp3_voice_test_*.mp3 - Olika Chirp3-HD röster att välja mellan")