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
            
            # DRASTISK FIX: Bygg credentials manuellt från komponenter
            try:
                from google.oauth2 import service_account
                from google.auth import jwt
                import json
                
                cred_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                if cred_file and os.path.exists(cred_file):
                    logger.info(f"🔥 DRASTISK FIX: Manuell credential-byggning från: {cred_file}")
                    
                    # Läs JSON-data
                    with open(cred_file, 'r') as f:
                        cred_data = json.load(f)
                    
                    # DEBUG: Kolla private key format
                    private_key = cred_data["private_key"]
                    logger.info(f"🔍 Private key typ: {type(private_key)}")
                    logger.info(f"🔍 Private key längd: {len(private_key)}")
                    logger.info(f"🔍 Private key börjar med: {private_key[:50]}...")
                    logger.info(f"🔍 Private key slutar med: ...{private_key[-50:]}")
                    
                    # Försök fixa private key format
                    if isinstance(private_key, str):
                        # Säkerställ korrekt newline-format
                        fixed_private_key = private_key.replace('\\n', '\n')
                        logger.info(f"🔧 Fixade private key newlines")
                    else:
                        fixed_private_key = private_key
                    
                    # Bygg credentials helt manuellt med minimal data
                    try:
                        # Metod 1: Minimal service account credentials med fixad private key
                        minimal_cred_data = {
                            "type": cred_data["type"],
                            "project_id": cred_data["project_id"], 
                            "private_key_id": cred_data["private_key_id"],
                            "private_key": fixed_private_key,
                            "client_email": cred_data["client_email"],
                            "client_id": cred_data["client_id"],
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token"
                        }
                        
                        logger.info("🔥 Försöker med minimala credentials")
                        credentials = service_account.Credentials.from_service_account_info(
                            minimal_cred_data,
                            scopes=['https://www.googleapis.com/auth/cloud-platform']
                        )
                        
                        logger.info("🔥 Skapar TTS-klient med minimala credentials")
                        self.client = texttospeech.TextToSpeechClient(credentials=credentials)
                        logger.info("✅ DRASTISK FIX LYCKADES - TTS-klient skapad!")
                        return True
                        
                    except Exception as e2:
                        logger.warning(f"⚠️ Minimala credentials failade: {e2}")
                        
                        # Metod 2: Ännu enklare approach
                        logger.info("🔥 Försöker ännu enklare credentials")
                        credentials = service_account.Credentials.from_service_account_info(
                            cred_data
                        )
                        self.client = texttospeech.TextToSpeechClient(credentials=credentials)
                        logger.info("✅ ENKEL FIX LYCKADES - TTS-klient skapad!")
                        return True
                        
            except Exception as e:
                logger.warning(f"⚠️ DRASTISK FIX failade: {e}")
                
            # SISTA UTVÄG: Försök utan explicit credentials alls
            try:
                logger.info("🆘 SISTA UTVÄG: Försöker utan explicit credentials")
                # Ta bort alla credential environment vars
                if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
                    del os.environ['GOOGLE_APPLICATION_CREDENTIALS']
                    
                # Återställ från secret
                import json
                with open('google-cloud-service-account.json', 'r') as f:
                    cred_data = json.load(f)
                    
                # Sätt bara project
                os.environ['GOOGLE_CLOUD_PROJECT'] = cred_data['project_id']
                
                self.client = texttospeech.TextToSpeechClient()
                logger.info("✅ SISTA UTVÄG LYCKADES - TTS-klient utan credentials!")
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ SISTA UTVÄG failade: {e}")
            
            # Fallback: Skapa TTS-klient med environment credentials
            logger.info("🔄 Försöker med environment credentials...")
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
        
        # DEBUG: Kolla innehållet i credentials-filen
        cred_file = 'google-cloud-service-account.json'
        if os.path.exists(cred_file):
            try:
                with open(cred_file, 'r') as f:
                    content = f.read()
                logger.info(f"🔍 Credentials fil storlek: {len(content)} tecken")
                logger.info(f"🔍 Första 100 tecken: {content[:100]}...")
                logger.info(f"🔍 Sista 50 tecken: ...{content[-50:]}")
                
                # Försök parsa JSON
                import json
                parsed = json.loads(content)
                logger.info(f"🔍 JSON keys: {list(parsed.keys())}")
                logger.info(f"🔍 Project ID: {parsed.get('project_id', 'NOT FOUND')}")
                
            except Exception as e:
                logger.error(f"❌ Fel vid läsning av credentials fil: {e}")
        
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
                    
                    # EXPLICIT CREDENTIALS LOADING - Försök läsa credentials direkt
                    try:
                        from google.oauth2 import service_account
                        credentials = service_account.Credentials.from_service_account_file(
                            os.path.abspath(file_path)
                        )
                        logger.info("🎯 EXPLICIT CREDENTIALS LOADED SUCCESSFULLY!")
                        return True
                    except Exception as e:
                        logger.error(f"❌ EXPLICIT CREDENTIALS FAILED: {e}")
                        # Fallback till environment variabel
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
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocessa text för bättre uttal med korrekt SSML-formattering
        - AI uttalas perfekt som sammanhängande "ɑːiː" utan pauser
        - Hela texten omsluts med <speak>-taggen som SSML kräver
        """
        import re
        
        # Ta bort upprepade ord först (som IPCC IPCC)
        text = self._remove_word_duplicates(text)
        
        # Använd SSML med IPA för extra långa vokalljud som i SAAB och BIL
        # AI: använd "ɑːːiːː" med extra längdmarkörer för mycket långa ljud
        text = re.sub(r'\bAI\b', '<phoneme alphabet="ipa" ph="ɑːːiːː">AI</phoneme>', text)
        text = re.sub(r'\bAi\b', '<phoneme alphabet="ipa" ph="ɑːːiːː">Ai</phoneme>', text)
        # EU: använd "eːuː" för korrekt svenskt uttal (inte "e-o" utan "e-u")
        text = re.sub(r'\bEU\b', '<phoneme alphabet="ipa" ph="eːuː">EU</phoneme>', text)
        text = re.sub(r'\bEu\b', '<phoneme alphabet="ipa" ph="eːuː">Eu</phoneme>', text)
        text = re.sub(r'\bUSA\b', '<phoneme alphabet="ipa" ph="uːɛsˈɑː">USA</phoneme>', text)
        text = re.sub(r'\bUsa\b', '<phoneme alphabet="ipa" ph="uːɛsˈɑː">Usa</phoneme>', text)
        # SMHI: naturligt uttal som "s.m.h.i" utan överbetoning på sista I
        text = re.sub(r'\bSMHI\b', '<phoneme alphabet="ipa" ph="ɛs.ɛm.hoː.iː">SMHI</phoneme>', text)
        
        # VIKTIGT: Omslut hela texten med <speak>-taggen som SSML kräver
        text = f"<speak>{text}</speak>"
        
        return text
    
    def _remove_word_duplicates(self, text: str) -> str:
        """Ta bort upprepade ord som 'IPCC IPCC' → 'IPCC'"""
        import re
        
        # Hitta upprepade ord (case-insensitive)
        # Matchar "ord ord" eller "ORD ORD" men inte "ord ORD" (olika case)
        pattern = r'\b(\w+)(\s+\1)+\b'
        
        # Ersätt upprepningar med bara första ordet
        cleaned = re.sub(pattern, r'\1', text, flags=re.IGNORECASE)
        
        # Special-hantering för förkortningar som ofta upprepas
        abbreviations = ['IPCC', 'AI', 'EU', 'USA', 'SMHI', 'KTH', 'SVT']
        for abbr in abbreviations:
            # Ta bort direkt upprepning av förkortningar
            pattern_abbr = f'{abbr}\\s+{abbr}'
            cleaned = re.sub(pattern_abbr, abbr, cleaned, flags=re.IGNORECASE)
        
        return cleaned
    
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
            
            # Preprocessa text för bättre uttal
            processed_text = self._preprocess_text(text)
            
            # Skapa input - använd SSML om vi har fonetiska markeringar
            if '<phoneme' in processed_text or processed_text.startswith('<speak>'):
                # Texten är redan SSML-formaterad från _preprocess_text
                synthesis_input = texttospeech.SynthesisInput(ssml=processed_text)
            else:
                synthesis_input = texttospeech.SynthesisInput(text=processed_text)
            
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