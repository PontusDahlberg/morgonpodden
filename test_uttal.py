#!/usr/bin/env python3
"""
Snabb test av AI-uttal och väder
"""
import os
import sys
import logging
from google_cloud_tts import GoogleCloudTTS

# Konfigurera logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_uttal():
    """Testa AI-uttal och grundläggande funktionalitet"""
    
    # Test-text som innehåller AI flera gånger
    test_text = """
    Lisa: Hej och välkommen till MMM Senaste Nytt! 
    
    Pelle: Tack Lisa! Idag ska vi prata om AI och hur AI-teknologi utvecklas. Enligt SMHI blir det bra väder.
    
    Lisa: Ja, AI är verkligen fascinerande. AI-forskning inom EU och USA går framåt snabbt.
    
    Pelle: Det stämmer! AI kommer att förändra mycket i vårt samhälle.
    
    Lisa: Tack för att du lyssnade på denna korta test av AI-uttal!
    """
    
    try:
        # Skapa TTS-instans
        logger.info("🎙️ Skapar TTS-instans...")
        tts = GoogleCloudTTS()
        
        # Generera audio
        output_file = "test_ai_uttal.mp3"
        logger.info(f"🗣️ Genererar audio med AI-uttal test...")
        
        # Generera audio med rätt metod
        audio_data = tts.generate_audio(
            text=test_text,
            voice="sanna"  # Lisa's röst
        )
        
        success = False
        if audio_data:
            with open(output_file, 'wb') as f:
                f.write(audio_data)
            success = True
        
        if success and os.path.exists(output_file):
            logger.info(f"✅ Test slutförd! Lyssna på: {output_file}")
            logger.info("🎯 Kontrollera att AI uttalas naturligt (inte 'aj' eller för separerat)")
            return True
        else:
            logger.error("❌ Misslyckades att generera audio")
            return False
            
    except Exception as e:
        logger.error(f"❌ Fel vid test: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Startar uttal-test...")
    success = test_uttal()
    if success:
        print("\n✅ Test slutfört! Kontrollera audio-filen.")
    else:
        print("\n❌ Test misslyckades.")