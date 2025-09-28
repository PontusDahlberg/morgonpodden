#!/usr/bin/env python3
"""
Test av Google Cloud Chirp3-HD röster i podcast-format
"""

import os
import sys
sys.path.append('.')

from google_tts_backup import create_google_podcast_service_account

def test_chirp3_podcast():
    """Testa att skapa en kort podcast med Chirp3-HD rösterna"""
    
    # Sätt upp credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-service-account.json'
    
    # Definiera test-segment
    test_segments = [
        {
            "voice": "sanna", 
            "text": "Välkommen till dagens test av de nya Chirp3-HD rösterna från Google Cloud TTS!"
        },
        {
            "voice": "george", 
            "text": "Ja, det här låter verkligen lovande! Kvaliteten verkar vara mycket bättre än de gamla WaveNet-rösterna."
        },
        {
            "voice": "sanna", 
            "text": "Och priset är fantastiskt - bara fyra dollar per miljon tecken jämfört med ElevenLabs sextiofem dollar!"
        },
        {
            "voice": "george", 
            "text": "Det här kan definitivt vara vår nya backup-lösning när ElevenLabs-krediterna tar slut."
        }
    ]
    
    print("🎙️ Testar Chirp3-HD podcast generation")
    print("=" * 50)
    
    result = create_google_podcast_service_account(test_segments)
    
    if result:
        print(f"\n✅ FRAMGÅNG! Podcast skapad: {result}")
        print("🎧 Lyssna och bedöm kvaliteten jämfört med WaveNet och OpenAI")
    else:
        print("\n❌ Något gick fel vid podcast-skapandet")

if __name__ == "__main__":
    test_chirp3_podcast()
