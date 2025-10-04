#!/usr/bin/env python3
"""
Förenklad Google Cloud TTS-integration för Människa Maskin Miljö
Primär TTS-leverantör som ersätter ElevenLabs
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
from google.cloud import texttospeech
from pydub import AudioSegment

logger = logging.getLogger(__name__)

class GoogleCloudTTS:
    """Google Cloud TTS-integration med Chirp3-HD röster"""
    
    def __init__(self):
        logger.info("🔥 GOOGLE CLOUD TTS VERSION 2.0 - BRUTAL FIX LOADED!")
        self.client = None
        self.voice_mapping = {
            # Primära röster för podcasten
            "sanna": {
                "name": "sv-SE-Chirp3-HD-Gacrux",     # Lisa - BÄSTA kvinnlig röst
                "gender": texttospeech.SsmlVoiceGender.FEMALE,
                "description": "Lisa (Gacrux) - Professionell kvinnlig röst"
            },
            "george": {
                "name": "sv-SE-Chirp3-HD-Iapetus",    # Pelle - BÄSTA manlig röst  
                "gender": texttospeech.SsmlVoiceGender.MALE,
                "description": "Pelle (Iapetus) - Professionell manlig röst"
            },
            # Bakåtkompatibilitet med andra namn
            "lisa": {
                "name": "sv-SE-Chirp3-HD-Gacrux",
                "gender": texttospeech.SsmlVoiceGender.FEMALE,
                "description": "Lisa (Gacrux) - Professionell kvinnlig röst"
            },
            "pelle": {
                "name": "sv-SE-Chirp3-HD-Iapetus",
                "gender": texttospeech.SsmlVoiceGender.MALE,
                "description": "Pelle (Iapetus) - Professionell manlig röst"
            }
        }
        
        self._init_client()
    
    def _init_client(self) -> bool:
        """Initialisera Google Cloud TTS-klient"""
        try:
            # Kontrollera credentials
            if not self._setup_credentials():
                return False
            
            # Skapa TTS-klient
            self.client = texttospeech.TextToSpeechClient()
            logger.info("✅ Google Cloud TTS-klient initialiserad")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fel vid initialisering av Google Cloud TTS: {e}")
            return False
    
    def _setup_credentials(self) -> bool:
        """Setup Google Cloud credentials - FORCE FILE MODE"""
        import json
        
        # UNIK IDENTIFIERARE - OM DU SER DETTA KÖR VI NY KOD!
        logger.info("🚀 BRUTAL FIX VERSION 2.0 - TVINGAR FIL-LÄGE!")
        
        # TEMPORÄR FIX: Ta bort GOOGLE_CLOUD_KEY helt för att tvinga fil-läge
        if 'GOOGLE_CLOUD_KEY' in os.environ:
            logger.info("🔧 Tar bort GOOGLE_CLOUD_KEY från environment för att tvinga fil-läge")
            del os.environ['GOOGLE_CLOUD_KEY']
        
        # Debug info
        logger.info(f"🔍 GOOGLE_APPLICATION_CREDENTIALS = {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
        logger.info(f"🔍 Working directory = {os.getcwd()}")
        logger.info(f"🔍 Files in directory = {os.listdir('.')}")
        
        # Prioritera absolut sökväg från environment
        credentials_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if credentials_file:
            logger.info(f"🔍 Testar credentials fil: {credentials_file}")
            if os.path.exists(credentials_file):
                logger.info(f"✅ ANVÄNDER SERVICE ACCOUNT FIL: {credentials_file}")
                return True
            else:
                logger.error(f"❌ Credentials fil finns inte: {credentials_file}")
        
        # Kolla standardplatser
        possible_files = [
            'google-cloud-service-account.json',
            './google-cloud-service-account.json',
            '/tmp/google-cloud-service-account.json'
        ]
        
        for file_path in possible_files:
            logger.info(f"🔍 Testar fil: {file_path}")
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Validera JSON
                    json.loads(content)
                    
                    # Sätt environment variabel
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.abspath(file_path)
                    logger.info(f"✅ ANVÄNDER FIL: {os.path.abspath(file_path)}")
                    return True
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Ogiltigt JSON i {file_path}: {e}")
                except Exception as e:
                    logger.error(f"❌ Fel vid läsning av {file_path}: {e}")
            else:
                logger.warning(f"⚠️ Fil finns inte: {file_path}")
        
        logger.error("❌ Inga Google Cloud credentials-filer hittade!")
        logger.error("❌ Kontrollera att google-cloud-service-account.json skapades korrekt")
        return False
    
    def is_available(self) -> bool:
        """Kontrollera om Google Cloud TTS är tillgängligt"""
        return self.client is not None
    
    def generate_audio(self, text: str, voice: str = "sanna") -> Optional[bytes]:
        """
        Generera audio med Google Cloud TTS
        
        Args:
            text: Text att konvertera
            voice: Röst att använda ("sanna", "george", "lisa", "pelle")
            
        Returns:
            Audio data som bytes, eller None vid fel
        """
        if not self.is_available():
            logger.error("❌ Google Cloud TTS inte tillgängligt")
            return None
        
        # Validera och välj röst
        if voice not in self.voice_mapping:
            logger.warning(f"⚠️ Okänd röst '{voice}', använder 'sanna'")
            voice = "sanna"
        
        voice_config = self.voice_mapping[voice]
        
        try:
            # Konfigurera röst
            voice_params = texttospeech.VoiceSelectionParams(
                language_code="sv-SE",
                name=voice_config["name"],
                ssml_gender=voice_config["gender"]
            )
            
            # Konfigurera audio (hög kvalitet)
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                sample_rate_hertz=24000,  # Hög kvalitet
                speaking_rate=1.0,        # Normal hastighet
                pitch=0.0,               # Normal pitch
                volume_gain_db=0.0       # Normal volym
            )
            
            # Skapa input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            logger.info(f"🎤 Genererar med {voice_config['description']}")
            logger.info(f"📝 Text ({len(text)} tecken): {text[:100]}...")
            
            # Anropa TTS
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config
            )
            
            logger.info(f"✅ Audio genererad ({len(response.audio_content)} bytes)")
            return response.audio_content
            
        except Exception as e:
            logger.error(f"❌ Fel vid audiogenerering: {e}")
            return None
    
    def generate_podcast_audio(self, segments: List[Dict]) -> Optional[str]:
        """
        Generera komplett podcast med flera segment
        
        Args:
            segments: Lista med segments [{"text": "...", "voice": "sanna"}, ...]
            
        Returns:
            Sökväg till genererad audiofil
        """
        if not self.is_available():
            return None
        
        logger.info(f"🎙️ Genererar podcast med {len(segments)} segment")
        
        audio_segments = []
        total_chars = 0
        
        # Skapa temp-mapp
        os.makedirs('audio/temp', exist_ok=True)
        
        try:
            # Generera varje segment
            for i, segment in enumerate(segments):
                text = segment.get('text', '')
                voice = segment.get('voice', 'sanna')
                
                if not text:
                    continue
                
                logger.info(f"🎤 Segment {i+1}/{len(segments)}: {voice}")
                
                # Generera audio för segmentet
                audio_data = self.generate_audio(text, voice)
                if not audio_data:
                    logger.warning(f"⚠️ Misslyckades generera segment {i+1}")
                    continue
                
                # Spara temporärt segment
                temp_file = f'audio/temp/segment_{i+1}.mp3'
                with open(temp_file, 'wb') as f:
                    f.write(audio_data)
                
                # Ladda med pydub för kombination
                audio_segment = AudioSegment.from_mp3(temp_file)
                audio_segments.append(audio_segment)
                total_chars += len(text)
                
                # Lägg till kort paus mellan segment
                if i < len(segments) - 1:  # Inte efter sista segmentet
                    pause = AudioSegment.silent(duration=500)  # 0.5 sekund
                    audio_segments.append(pause)
            
            if not audio_segments:
                logger.error("❌ Inga segment kunde genereras")
                return None
            
            # Kombinera alla segment
            logger.info("🔗 Kombinerar audiosegment...")
            combined = AudioSegment.empty()
            for segment in audio_segments:
                combined += segment
            
            # Spara slutligt resultat
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f'audio/MMM_google_cloud_{timestamp}.mp3'
            combined.export(output_file, format="mp3")
            
            # Rensa temp-filer
            try:
                import glob
                for temp_file in glob.glob('audio/temp/segment_*.mp3'):
                    os.remove(temp_file)
            except:
                pass
            
            # Rapportera resultat
            duration_minutes = len(combined) / 60000
            cost = total_chars * 0.000004  # $4 per 1M chars för Chirp3-HD
            
            logger.info(f"✅ Podcast genererad: {output_file}")
            logger.info(f"🕐 Längd: {duration_minutes:.1f} minuter")
            logger.info(f"📊 Totalt tecken: {total_chars:,}")
            logger.info(f"💰 Uppskattad kostnad: ${cost:.4f}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"❌ Fel vid podcast-generering: {e}")
            return None
    
    def estimate_cost(self, text_length: int) -> Dict:
        """Uppskatta kostnad för TTS-generering"""
        cost_per_char = 0.000004  # $4 per 1M chars för Chirp3-HD
        cost = text_length * cost_per_char
        
        return {
            "characters": text_length,
            "cost_usd": cost,
            "cost_description": "Google Cloud TTS Chirp3-HD",
            "rate": "$4.00 per 1M characters"
        }

def test_google_cloud_tts():
    """Testa Google Cloud TTS-funktionalitet"""
    print("🧪 Testar Google Cloud TTS...")
    
    tts = GoogleCloudTTS()
    
    if not tts.is_available():
        print("❌ Google Cloud TTS inte tillgängligt")
        return False
    
    # Testa enskilda röster
    test_voices = ["sanna", "george"]
    for voice in test_voices:
        print(f"\n🎤 Testar röst: {voice}")
        
        text = f"Hej, jag är {voice} och testar Google Cloud TTS med Chirp3-HD röster för Människa Maskin Miljö podcast."
        audio_data = tts.generate_audio(text, voice)
        
        if audio_data:
            # Spara test-fil
            test_file = f"audio/test_google_{voice}.mp3"
            os.makedirs('audio', exist_ok=True)
            with open(test_file, 'wb') as f:
                f.write(audio_data)
            print(f"✅ Test lyckades: {test_file}")
        else:
            print(f"❌ Test misslyckades för {voice}")
    
    # Testa podcast-generering
    print("\n🎙️ Testar podcast-generering...")
    test_segments = [
        {"text": "Välkommen till dagens test av Google Cloud TTS för Människa Maskin Miljö!", "voice": "sanna"},
        {"text": "Kvaliteten på Chirp3-HD rösterna är verkligen imponerande, och priset är fantastiskt lågt.", "voice": "george"},
        {"text": "Med bara fyra dollar per miljon tecken kan vi skapa professionella podcasts mycket kostnadseffektivt.", "voice": "sanna"},
        {"text": "Detta är definitivt framtiden för automatisk podcast-generering!", "voice": "george"}
    ]
    
    podcast_file = tts.generate_podcast_audio(test_segments)
    if podcast_file:
        print(f"✅ Test-podcast skapad: {podcast_file}")
        return True
    else:
        print("❌ Podcast-test misslyckades")
        return False

if __name__ == "__main__":
    test_google_cloud_tts()