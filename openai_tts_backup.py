#!/usr/bin/env python3
"""
OpenAI TTS backup för Människa Maskin Miljö podcast
12x billigare än ElevenLabs!
"""

import os
import requests
import logging
from typing import Dict, List, Optional
from pydub import AudioSegment

logger = logging.getLogger(__name__)

class OpenAITTSGenerator:
    """OpenAI TTS som backup för ElevenLabs"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY saknas i miljövariabler")
    
    def generate_audio(self, text: str, voice: str = "nova", model: str = "tts-1") -> bytes:
        """
        Generera audio med OpenAI TTS
        
        Args:
            text: Text att konvertera
            voice: alloy, echo, fable, onyx, nova, shimmer
            model: tts-1 (snabbt) eller tts-1-hd (högre kvalitet)
        """
        url = "https://api.openai.com/v1/audio/speech"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": "mp3"
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            logger.info(f"✅ OpenAI TTS genererat: {len(response.content)} bytes")
            return response.content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ OpenAI TTS fel: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise

def create_podcast_with_openai_tts(segments: List[Dict]) -> str:
    """
    Skapa podcast med OpenAI TTS som backup
    
    Args:
        segments: Lista med {'text': str, 'voice': str}
    
    Returns:
        Sökväg till skapad audio-fil
    """
    
    print("🎙️ Skapar podcast med OpenAI TTS...")
    
    tts = OpenAITTSGenerator()
    
    # Röstmappning (närmare ElevenLabs-rösterna)
    voice_mapping = {
        'sanna': 'nova',     # Kvinna, neutral och professionell
        'george': 'onyx',    # Man, djup och varm
        'female': 'nova',
        'male': 'onyx'
    }
    
    audio_segments = []
    
    for i, segment in enumerate(segments, 1):
        text = segment.get('text', '')
        voice_name = segment.get('voice', 'sanna').lower()
        
        # Mappa till OpenAI röst
        openai_voice = voice_mapping.get(voice_name, 'nova')
        
        print(f"🎤 Segment {i}: {voice_name} ({openai_voice}) - {text[:50]}...")
        
        try:
            # Generera audio
            audio_data = tts.generate_audio(text, voice=openai_voice)
            
            # Konvertera till AudioSegment
            with open(f'temp_segment_{i}.mp3', 'wb') as f:
                f.write(audio_data)
            
            segment_audio = AudioSegment.from_mp3(f'temp_segment_{i}.mp3')
            audio_segments.append(segment_audio)
            
            # Rensa upp temp-fil
            os.remove(f'temp_segment_{i}.mp3')
            
            # Lägg till paus mellan segment (1 sekund)
            if i < len(segments):
                pause = AudioSegment.silent(duration=1000)
                audio_segments.append(pause)
            
        except Exception as e:
            logger.error(f"❌ Fel vid generering av segment {i}: {e}")
            continue
    
    if not audio_segments:
        raise ValueError("Inga segment kunde genereras")
    
    # Sätt ihop alla segment
    final_audio = sum(audio_segments)
    
    # Spara final audio
    output_file = "audio/episode_openai_backup.mp3"
    final_audio.export(output_file, format="mp3")
    
    duration_minutes = len(final_audio) / 60000
    print(f"✅ Podcast skapad: {output_file}")
    print(f"🕐 Längd: {duration_minutes:.1f} minuter")
    print(f"💰 Uppskattad kostnad: ~${len(' '.join(s.get('text', '') for s in segments)) * 0.000015:.3f}")
    
    return output_file

def test_openai_voices():
    """Testa alla OpenAI röster på svenska"""
    
    test_text = "Hej och välkommen till Människa Maskin Miljö! Detta är en test av olika röster."
    
    voices = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
    
    tts = OpenAITTSGenerator()
    
    print("🎭 Testar OpenAI röster på svenska:")
    
    for voice in voices:
        try:
            print(f"  🎤 Testar {voice}...")
            audio_data = tts.generate_audio(test_text, voice=voice)
            
            with open(f'audio/test_{voice}.mp3', 'wb') as f:
                f.write(audio_data)
            
            print(f"     ✅ Sparad: audio/test_{voice}.mp3 ({len(audio_data)} bytes)")
            
        except Exception as e:
            print(f"     ❌ Fel: {e}")

if __name__ == "__main__":
    print("🔄 OpenAI TTS Backup Test")
    print("=" * 40)
    
    # Testa alla röster
    if os.getenv('OPENAI_API_KEY'):
        test_openai_voices()
        
        # Testa podcast-skapande
        test_segments = [
            {"text": "Välkommen till Människa Maskin Miljö, vecka test!", "voice": "sanna"},
            {"text": "Idag har vi spännande nyheter om artificiell intelligens och miljöteknik.", "voice": "george"},
            {"text": "Svenska forskare har gjort ett genombrott inom batteriutveckling.", "voice": "sanna"},
            {"text": "Detta kan revolutionera hur vi lagrar förnybar energi.", "voice": "george"}
        ]
        
        create_podcast_with_openai_tts(test_segments)
        
    else:
        print("⚠️ OPENAI_API_KEY saknas - lägg till i .env filen")
