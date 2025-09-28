#!/usr/bin/env python3
"""
TTS Manager - Nu med Google Cloud som primär TTS leverantör!
ElevenLabs är nu reserverad för andra användningsområden.
"""

import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

def should_use_google_cloud() -> bool:
    """Kontrollera om vi ska använda Google Cloud TTS (default: JA)"""
    use_google = os.getenv('USE_GOOGLE_CLOUD_TTS', 'true').lower()
    
    if use_google == 'true':
        return True
    
    # Fallback kontroll
    google_creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if google_creds and os.path.exists(google_creds):
        logger.info("✅ Google Cloud credentials hittade, använder Google TTS")
        return True
        
    logger.warning("⚠️ Google Cloud TTS inte tillgängligt, faller tillbaka på backup")
    return False
        
    except Exception as e:
        logger.warning(f"⚠️ Kunde inte kontrollera ElevenLabs status: {e}")
        return True

def generate_tts_audio(text: str, voice_type: str = "sanna", emotion: str = "professional") -> bytes:
    """
    Generera TTS audio med fallback-system
    
    Args:
        text: Text att konvertera
        voice_type: "sanna" eller "george" 
        emotion: "professional", "exciting", "serious", "friendly"
    
    Returns:
        Audio data som bytes
    """
    
    if should_use_backup():
        logger.info("🔄 Använder OpenAI TTS (backup)")
        return generate_openai_tts(text, voice_type)
    else:
        logger.info("🎭 Använder ElevenLabs TTS")
        return generate_elevenlabs_tts(text, voice_type, emotion)

def generate_openai_tts(text: str, voice_type: str) -> bytes:
    """Generera med OpenAI TTS"""
    import requests
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY saknas för backup")
    
    # Röstmappning
    voice_mapping = {
        'sanna': 'nova',   # Kvinna, neutral
        'george': 'onyx',  # Man, djup  
        'female': 'nova',
        'male': 'onyx'
    }
    
    openai_voice = voice_mapping.get(voice_type.lower(), 'nova')
    
    url = "https://api.openai.com/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "tts-1",  # Snabbare och billigare
        "input": text,
        "voice": openai_voice,
        "response_format": "mp3"
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    
    logger.info(f"✅ OpenAI TTS: {len(response.content)} bytes för {len(text)} tecken")
    return response.content

def generate_elevenlabs_tts(text: str, voice_type: str, emotion: str) -> bytes:
    """Generera med ElevenLabs TTS (original system)"""
    
    # Import original ElevenLabs function
    from run_podcast import generate_audio_with_voice_settings
    
    # Röst-ID mappning
    voice_ids = {
        'sanna': os.getenv('ELEVENLABS_VOICE_ID_SANNA'),
        'george': os.getenv('ELEVENLABS_VOICE_ID_GEORGE')
    }
    
    voice_id = voice_ids.get(voice_type.lower(), voice_ids['sanna'])
    
    # Hämta emotion settings
    from emotion_analyzer import get_voice_settings
    voice_settings = get_voice_settings(emotion)
    
    return generate_audio_with_voice_settings(text, voice_id, voice_settings)

# Test function
if __name__ == "__main__":
    print("🔧 TTS Backup Manager Test")
    print("=" * 40)
    
    # Test backup detection
    backup_status = should_use_backup()
    print(f"Använd backup: {backup_status}")
    
    # Test text
    test_text = "Detta är en test av backup TTS-systemet för Människa Maskin Miljö."
    
    try:
        audio_data = generate_tts_audio(test_text, "sanna", "professional")
        
        with open('audio/test_backup_system.mp3', 'wb') as f:
            f.write(audio_data)
        
        print(f"✅ Test lyckades: {len(audio_data)} bytes")
        print("📁 Sparad som: audio/test_backup_system.mp3")
        
    except Exception as e:
        print(f"❌ Test misslyckades: {e}")
