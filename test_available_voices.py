#!/usr/bin/env python3
"""
Test script to check all available Swedish voices in Google Cloud TTS
and categorize them by type (Chirp3-HD, Studio, WaveNet, Neural2, etc.)
"""

import os
from google.cloud import texttospeech

# Set up Google Cloud credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-service-account.json'

def list_swedish_voices():
    """List all available Swedish voices and their features."""
    client = texttospeech.TextToSpeechClient()
    
    # Fetch all available voices
    voices = client.list_voices()
    
    # Filter Swedish voices and categorize them
    swedish_voices = {}
    voice_types = {
        'Chirp3-HD': [],
        'Studio': [],
        'Journey': [],
        'Neural2': [],
        'WaveNet': [],
        'Standard': [],
        'Other': []
    }
    
    for voice in voices.voices:
        for language_code in voice.language_codes:
            if language_code.startswith('sv-'):  # Swedish voices
                voice_info = {
                    'name': voice.name,
                    'language_codes': list(voice.language_codes),
                    'ssml_gender': voice.ssml_gender.name,
                    'natural_sample_rate_hertz': voice.natural_sample_rate_hertz
                }
                
                # Categorize by voice type
                if 'Chirp3' in voice.name:
                    voice_types['Chirp3-HD'].append(voice_info)
                elif 'Studio' in voice.name:
                    voice_types['Studio'].append(voice_info)
                elif 'Journey' in voice.name:
                    voice_types['Journey'].append(voice_info)
                elif 'Neural2' in voice.name:
                    voice_types['Neural2'].append(voice_info)
                elif 'Wavenet' in voice.name:
                    voice_types['WaveNet'].append(voice_info)
                elif 'Standard' in voice.name:
                    voice_types['Standard'].append(voice_info)
                else:
                    voice_types['Other'].append(voice_info)
    
    return voice_types

def test_studio_voice_with_ssml():
    """Test if Studio voices support SSML and dynamic content."""
    client = texttospeech.TextToSpeechClient()
    
    # Test text with various SSML features
    ssml_text = """
    <speak>
        <p>
            <prosody rate="fast" pitch="+2st" volume="loud">
                Hej och välkomna till vår morgonpodd!
            </prosody>
        </p>
        
        <break time="1s"/>
        
        <p>
            <prosody rate="slow" pitch="-1st">
                Nu blir det lite mer seriöst när vi pratar om dagens nyheter.
            </prosody>
        </p>
        
        <break time="500ms"/>
        
        <p>
            <emphasis level="strong">Detta är verkligen viktigt att komma ihåg!</emphasis>
        </p>
        
        <p>
            <prosody rate="medium" pitch="default">
                Och så avslutar vi med en vanlig ton igen.
            </prosody>
        </p>
    </speak>
    """
    
    return ssml_text

def main():
    print("🎙️ Checking available Swedish voices in Google Cloud TTS...\n")
    
    try:
        voice_types = list_swedish_voices()
        
        for voice_type, voices in voice_types.items():
            if voices:  # Only show categories that have voices
                print(f"\n📢 {voice_type} Voices ({len(voices)} found):")
                print("=" * 50)
                for voice in voices:
                    print(f"  • {voice['name']}")
                    print(f"    Languages: {', '.join(voice['language_codes'])}")
                    print(f"    Gender: {voice['ssml_gender']}")
                    print(f"    Sample Rate: {voice['natural_sample_rate_hertz']} Hz")
                    print()
        
        # Check if we have Studio voices
        if voice_types['Studio']:
            print("\n🎉 Studio voices found! These should support SSML with better quality than WaveNet.")
            print("Let's test one with SSML...")
            
            test_ssml = test_studio_voice_with_ssml()
            print("\nTest SSML content prepared:")
            print(test_ssml)
            
        elif voice_types['Journey']:
            print("\n🚀 Journey voices found! These might be newer than WaveNet.")
            
        else:
            print("\n❌ No Studio or Journey voices found for Swedish.")
            print("Available options are limited to Chirp3-HD (no SSML) and WaveNet (with SSML).")
    
    except Exception as e:
        print(f"❌ Error checking voices: {e}")
        print("\nMake sure you have Google Cloud credentials set up properly.")

if __name__ == "__main__":
    main()