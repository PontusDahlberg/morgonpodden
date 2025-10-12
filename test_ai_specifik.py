#!/usr/bin/env python3
"""
Specifik test av AI-uttal med SSML
"""
import os
import logging
from google_cloud_tts import GoogleCloudTTS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ai_uttal_specifik():
    """Testa exakt AI-uttalet med olika varianter"""
    
    # Korta meningar som fokuserar på AI-uttalet
    test_sentences = [
        "AI är framtiden.",
        "Vi pratar om AI idag.", 
        "AI-teknologi utvecklas snabbt.",
        "AI och maskinlärning.",
        "Jag använder AI varje dag."
    ]
    
    try:
        tts = GoogleCloudTTS()
        
        for i, sentence in enumerate(test_sentences, 1):
            logger.info(f"🗣️ Testar mening {i}: {sentence}")
            
            audio_data = tts.generate_audio(
                text=sentence,
                voice="sanna"
            )
            
            if audio_data:
                output_file = f"test_ai_{i}.mp3"
                with open(output_file, 'wb') as f:
                    f.write(audio_data)
                logger.info(f"✅ Genererad: {output_file}")
            else:
                logger.error(f"❌ Misslyckades med mening {i}")
                
        logger.info("🎯 Lyssna på alla test_ai_*.mp3 filer för att jämföra uttalet")
        return True
        
    except Exception as e:
        logger.error(f"❌ Fel vid AI-uttal test: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Startar specifikt AI-uttal test...")
    success = test_ai_uttal_specifik()
    if success:
        print("\n✅ AI-uttal test slutfört!")
    else:
        print("\n❌ AI-uttal test misslyckades.")