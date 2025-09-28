#!/usr/bin/env python3
"""
Test intelligent SSML with WaveNet voices
"""

import os
from google.cloud import texttospeech

# Set up Google Cloud credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-service-account.json'

def test_intelligent_ssml_with_wavenet():
    """Test our intelligent SSML with WaveNet voices"""
    
    client = texttospeech.TextToSpeechClient()
    
    # Read the intelligent SSML
    with open('intelligent_ssml_sample.txt', 'r', encoding='utf-8') as f:
        ssml_content = f.read()
    
    print("🎭 Testing Intelligent SSML with WaveNet voices...")
    print(f"SSML Length: {len(ssml_content)} characters")
    
    # Test with different WaveNet voices
    voices_to_test = [
        ('sv-SE-Wavenet-A', 'FEMALE', 'Lisa-liknande'),
        ('sv-SE-Wavenet-C', 'MALE', 'Pelle-liknande'),
    ]
    
    for voice_name, gender, description in voices_to_test:
        print(f"\n🎤 Testing {voice_name} ({description})...")
        
        # Configure voice
        voice = texttospeech.VoiceSelectionParams(
            language_code="sv-SE",
            name=voice_name,
            ssml_gender=texttospeech.SsmlVoiceGender[gender]
        )
        
        # Configure audio
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0,
        )
        
        try:
            # Create synthesis request with SSML
            synthesis_input = texttospeech.SynthesisInput(ssml=ssml_content)
            
            # Perform TTS request
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Save audio
            filename = f"intelligent_ssml_{voice_name.lower().replace('-', '_')}.mp3"
            with open(f"audio/{filename}", "wb") as out:
                out.write(response.audio_content)
            
            print(f"✅ Generated: audio/{filename}")
            
            # Cost estimation
            cost = len(ssml_content) * 0.000016  # $16 per 1M chars
            print(f"💰 Estimated cost: ${cost:.4f}")
            
        except Exception as e:
            print(f"❌ Error with {voice_name}: {e}")

def compare_with_chirp3():
    """Compare with Chirp3-HD baseline (no SSML)"""
    
    client = texttospeech.TextToSpeechClient()
    
    # Plain text version (no SSML)
    plain_text = """
    Hej och välkomna till vår morgonpodd! 
    
    Idag ska vi prata om något verkligen spännande - vi har hittat en ny artist som kommer att förändra hela musikscenen. 
    
    Men först... lite mer seriösa nyheter. Situationen i världen just nu kräver vår uppmärksamhet.
    
    Det här är verkligen viktigt att komma ihåg, alla lyssnare!
    
    Men nu tillbaka till den glada stämningen - vi avslutar med veckans bästa låt!
    """
    
    print("\n🆚 Comparing with Chirp3-HD (no emotion)...")
    
    # Test Chirp3-HD Lisa equivalent
    voice = texttospeech.VoiceSelectionParams(
        language_code="sv-SE",
        name="sv-SE-Chirp3-HD-Aoede",  # Female voice similar to Lisa
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
    )
    
    try:
        synthesis_input = texttospeech.SynthesisInput(text=plain_text)
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Save for comparison
        with open("audio/chirp3_hd_comparison_no_emotion.mp3", "wb") as out:
            out.write(response.audio_content)
        
        print("✅ Generated: audio/chirp3_hd_comparison_no_emotion.mp3")
        
        cost = len(plain_text) * 0.000004  # $4 per 1M chars
        print(f"💰 Chirp3-HD cost: ${cost:.4f}")
        
    except Exception as e:
        print(f"❌ Error with Chirp3-HD: {e}")

def main():
    print("🎯 Testing Intelligent SSML vs Standard TTS")
    print("="*60)
    
    # Test intelligent SSML with WaveNet
    test_intelligent_ssml_with_wavenet()
    
    # Compare with Chirp3-HD
    compare_with_chirp3()
    
    print("\n📊 Summary:")
    print("• Intelligent SSML + WaveNet = Emotional control, 4x cost")
    print("• Chirp3-HD = Better voice quality, no emotion, 1x cost")
    print("• Listen to both and decide what works best for your podcast!")

if __name__ == "__main__":
    main()