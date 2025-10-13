#!/usr/bin/env python3
"""
Test av X-SAMPA AI-uttal
"""
import os
import logging
from google_cloud_tts import GoogleCloudTTS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_xsampa_ai():
    """Testa X-SAMPA AI-uttal med A:i:"""
    
    test_sentences = [
        "AI är framtiden.",
        "Vi använder AI dagligen.",
        "AI-teknologi utvecklas.",
        "Det här handlar om AI.",
        "Artificiell intelligens eller AI."
    ]
    
    try:
        tts = GoogleCloudTTS()
        
        for i, sentence in enumerate(test_sentences, 1):
            logger.info(f"🗣️ Test {i}: {sentence}")
            
            audio_data = tts.generate_audio(
                text=sentence,
                voice="sanna"
            )
            
            if audio_data:
                output_file = f"test_xsampa_ai_{i}.mp3"
                with open(output_file, 'wb') as f:
                    f.write(audio_data)
                logger.info(f"✅ Genererad: {output_file}")
            else:
                logger.error(f"❌ Misslyckades med test {i}")
        
        logger.info("🎧 Lyssna på test_xsampa_ai_*.mp3 för att höra X-SAMPA A:i: uttalet")
        return True
        
    except Exception as e:
        logger.error(f"❌ X-SAMPA test misslyckades: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testar X-SAMPA AI-uttal (A:i:)...")
    success = test_xsampa_ai()
    if success:
        print("✅ X-SAMPA test slutfört!")
    else:
        print("❌ X-SAMPA test misslyckades.")