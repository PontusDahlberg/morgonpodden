#!/usr/bin/env python3
"""
Test av korrekt IPA AI-uttal med specialtecken
"""
import os
import logging
from google_cloud_tts import GoogleCloudTTS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_correct_ipa_ai():
    """Testa korrekt IPA AI-uttal med ɑːiː"""
    
    test_sentences = [
        "AI är framtiden.",
        "Vi använder AI dagligen.",
        "AI-teknologi utvecklas.",
        "Det här handlar om AI.",
        "Artificiell intelligens eller AI."
    ]
    
    try:
        tts = GoogleCloudTTS()
        
        print("🔤 Testar IPA med specialtecken: ɑːiː")
        print("   ɑ = Script A (inte vanligt 'a')")
        print("   ː = Triangular colon (inte vanligt ':')")
        print("   iː = Långt i-ljud")
        print()
        
        for i, sentence in enumerate(test_sentences, 1):
            logger.info(f"🗣️ IPA Test {i}: {sentence}")
            
            audio_data = tts.generate_audio(
                text=sentence,
                voice="sanna"
            )
            
            if audio_data:
                output_file = f"test_correct_ipa_ai_{i}.mp3"
                with open(output_file, 'wb') as f:
                    f.write(audio_data)
                logger.info(f"✅ Genererad: {output_file}")
            else:
                logger.error(f"❌ Misslyckades med test {i}")
        
        logger.info("🎧 Lyssna på test_correct_ipa_ai_*.mp3")
        logger.info("🎯 Kontrollera att både A och I låter långa och tydliga")
        return True
        
    except Exception as e:
        logger.error(f"❌ IPA test misslyckades: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testar korrekt IPA AI-uttal (ɑːiː)...")
    success = test_correct_ipa_ai()
    if success:
        print("✅ Korrekt IPA test slutfört!")
    else:
        print("❌ IPA test misslyckades.")