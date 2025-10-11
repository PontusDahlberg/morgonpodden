#!/usr/bin/env python3
"""
ENKEL TTS-WRAPPER SOM BARA ANVÄNDER FIL
Testar att åsidosätta Google Cloud TTS-problemet
"""

import os
import json
import logging
from google.cloud import texttospeech

logger = logging.getLogger(__name__)

class SimpleGoogleCloudTTS:
    """Förenklad Google Cloud TTS som bara använder fil"""
    
    def __init__(self):
        logger.info("🔥 SIMPLE TTS VERSION - STARTING!")
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initiera TTS-klient med endast fil-baserade credentials"""
        try:
            # Bara leta efter filen, inget annat
            credential_files = [
                'google-cloud-service-account.json',
                './google-cloud-service-account.json',
                os.path.abspath('google-cloud-service-account.json')
            ]
            
            for cred_file in credential_files:
                if os.path.exists(cred_file):
                    logger.info(f"🎯 HITTADE CREDENTIALS FIL: {cred_file}")
                    
                    # Läs och validera filen
                    with open(cred_file, 'r') as f:
                        cred_data = json.load(f)
                    
                    # Sätt environment variabel
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.abspath(cred_file)
                    
                    # Skapa klient
                    self.client = texttospeech.TextToSpeechClient()
                    logger.info("✅ SIMPLE TTS CLIENT INITIALIZED!")
                    return
                else:
                    logger.warning(f"⚠️ Fil finns inte: {cred_file}")
            
            raise Exception("Ingen credentials-fil hittad!")
            
        except Exception as e:
            logger.error(f"❌ SIMPLE TTS FAILED: {e}")
            raise
    
    def is_available(self):
        return self.client is not None

# Test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tts = SimpleGoogleCloudTTS()
    print(f"TTS available: {tts.is_available()}")