#!/usr/bin/env python3
"""
Test av extra långt AI-uttal med tystnad i början
"""
import os
import logging
from google_cloud_tts import GoogleCloudTTS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_extra_long_ai():
    """Testa extra långt AI-uttal med tystnad för ljudspelaren"""
    
    test_sentences = [
        # Lägg till tystnad i början så ljudspelaren hinner med
        "... ... ... AI är framtiden.",
        "... ... ... Vi använder AI dagligen.",
        "... ... ... AI-teknologi utvecklas.",
        "... ... ... Det här handlar om AI.",
        "... ... ... Artificiell intelligens eller AI."
    ]
    
    try:
        tts = GoogleCloudTTS()
        
        print("🔤 Testar extra långt AI-uttal: ɑːːiːː")
        print("   ɑːː = Extra långt A-ljud som i SAAB")  
        print("   iːː = Extra långt I-ljud som i BIL")
        print("   ... = Tystnad i början för ljudspelare")
        print()
        
        for i, sentence in enumerate(test_sentences, 1):
            logger.info(f"🗣️ Extra Long Test {i}: {sentence}")
            
            audio_data = tts.generate_audio(
                text=sentence,
                voice="sanna"
            )
            
            if audio_data:
                output_file = f"test_extra_long_ai_{i}.mp3"
                with open(output_file, 'wb') as f:
                    f.write(audio_data)
                logger.info(f"✅ Genererad: {output_file}")
            else:
                logger.error(f"❌ Misslyckades med test {i}")
        
        logger.info("🎧 Lyssna på test_extra_long_ai_*.mp3")
        logger.info("🎯 Kontrollera att AI uttalas som SAAB + BIL (extra långa ljud)")
        logger.info("⏱️ Kontrollera att det finns tystnad i början")
        return True
        
    except Exception as e:
        logger.error(f"❌ Extra long test misslyckades: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testar extra långt AI-uttal (ɑːːiːː) med tystnad...")
    success = test_extra_long_ai()
    if success:
        print("✅ Extra long AI test slutfört!")
    else:
        print("❌ Extra long test misslyckades.")