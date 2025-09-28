#!/usr/bin/env python3
"""
Test av nya karaktärerna Lisa och Pelle med Google Cloud Chirp3-HD
"""

import os
import sys
sys.path.append('.')

from google_tts_backup import create_google_podcast_service_account

def test_lisa_och_pelle():
    """Testa de nya karaktärerna Lisa (Gacrux) och Pelle (Iapetus)"""
    
    # Sätt upp credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-service-account.json'
    
    # Definiera test-segment med nya karaktärerna
    test_segments = [
        {
            "voice": "lisa", 
            "text": "Hej och välkommen till MMM Senaste Nytt! Jag heter Lisa och det här är vårt första dagliga avsnitt."
        },
        {
            "voice": "pelle", 
            "text": "Hej! Och jag heter Pelle. Nu när vi har bytt till Google Cloud TTS kan vi sända dagligen istället för bara en gång i veckan!"
        },
        {
            "voice": "lisa", 
            "text": "Precis! Med kostnader som är fyrtiofem gånger lägre än ElevenLabs kan vi utan problem göra tio minuter varje dag. Dagens nyheter kommer från svenska, europeiska och internationella källor."
        },
        {
            "voice": "pelle", 
            "text": "Och vi kommer alltid att ange våra källor så att ni lyssnare vet var informationen kommer från. Det är viktigt för oss att vara transparenta!"
        },
        {
            "voice": "lisa",
            "text": "Så välkommen till den nya eran av MMM - från veckonytt till senaste nytt, varje dag!"
        }
    ]
    
    print("🎙️ Testar Lisa och Pelle - de nya rösterna för MMM Senaste Nytt")
    print("=" * 65)
    
    result = create_google_podcast_service_account(test_segments)
    
    if result:
        print(f"\n✅ FRAMGÅNG! Testpodd med Lisa och Pelle: {result}")
        print("🎧 Lyssna för att höra hur de nya karaktärerna låter!")
        print("\n💡 Lisa: sv-SE-Chirp3-HD-Gacrux (bästa kvinnliga rösten)")
        print("💡 Pelle: sv-SE-Chirp3-HD-Iapetus (bästa manliga rösten)")
    else:
        print("\n❌ Något gick fel vid test-podcast skapandet")

if __name__ == "__main__":
    test_lisa_och_pelle()
