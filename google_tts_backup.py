#!/usr/bin/env python3
"""
Google Cloud TTS test med Service Account
Billigast och bäst för svenska röster!
"""

import os
import json
import base64
import logging
from typing import Dict, List
from google.cloud import texttospeech

logger = logging.getLogger(__name__)

def setup_google_credentials():
    """Setup Google Cloud credentials från service account key"""
    
    # Kolla om credentials finns som fil
    credentials_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if credentials_file and os.path.exists(credentials_file):
        print(f"✅ Använder credentials från fil: {credentials_file}")
        return True
    
    # Kolla om credentials finns som JSON i miljövariabel
    credentials_json = os.getenv('GOOGLE_CLOUD_CREDENTIALS_JSON')
    if credentials_json:
        try:
            # Spara JSON till temporär fil
            with open('google_credentials.json', 'w') as f:
                f.write(credentials_json)
            
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google_credentials.json'
            print("✅ Använder credentials från JSON miljövariabel")
            return True
            
        except Exception as e:
            print(f"❌ Fel vid setup av JSON credentials: {e}")
            return False
    
    print("⚠️ Inga Google Cloud credentials hittade")
    print("Sätt antingen:")
    print("1. GOOGLE_APPLICATION_CREDENTIALS=sökväg/till/service-account.json")
    print("2. GOOGLE_CLOUD_CREDENTIALS_JSON='{hela json innehållet}'")
    return False

def generate_google_tts_audio(text, voice="sanna", output_file="audio/google_tts_output.mp3"):
    """
    Generera audio med Google Cloud TTS (Service Account) - använder Chirp3-HD röster!
    
    Args:
        text: Texten att konvertera till tal
        voice: Röstnamn ("sanna" eller "george")
        output_file: Fil att spara audio till
    """
    
    # Konfigurera Google Cloud credentials
    if not setup_google_credentials():
        return None
    
    try:
        # Skapa TTS client
        client = texttospeech.TextToSpeechClient()
        
        # CHIRP3-HD röstmappning (högsta kvalitet!) - NYA KARAKTÄRER!
        voice_mapping = {
            "lisa": {
                "name": "sv-SE-Chirp3-HD-Gacrux",    # BÄSTA kvinnlig röst enligt test
                "gender": texttospeech.SsmlVoiceGender.FEMALE,
                "description": "Lisa (Gacrux) - Chirp3-HD kvinna (bästa kvalitet)"
            },
            "pelle": {
                "name": "sv-SE-Chirp3-HD-Iapetus",   # BÄSTA manlig röst enligt test  
                "gender": texttospeech.SsmlVoiceGender.MALE,
                "description": "Pelle (Iapetus) - Chirp3-HD man (bästa kvalitet)"
            },
            # Bakåtkompatibilitet med gamla namn
            "sanna": {
                "name": "sv-SE-Chirp3-HD-Gacrux", 
                "gender": texttospeech.SsmlVoiceGender.FEMALE,
                "description": "Lisa (Gacrux) - Chirp3-HD kvinna"
            },
            "george": {
                "name": "sv-SE-Chirp3-HD-Iapetus",
                "gender": texttospeech.SsmlVoiceGender.MALE,
                "description": "Pelle (Iapetus) - Chirp3-HD man"
            }
        }
        
        # Välj röst
        if voice not in voice_mapping:
            print(f"⚠️  Okänd röst '{voice}', använder 'sanna' som default")
            voice = "sanna"
        
        selected_voice = voice_mapping[voice]
        
        print(f"🎤 Genererar med {selected_voice['description']}")
        
        # Konfigurera voice selection
        voice_params = texttospeech.VoiceSelectionParams(
            language_code="sv-SE",
            name=selected_voice["name"],
            ssml_gender=selected_voice["gender"]
        )
        
        # Konfigurera audio output (högsta kvalitet)
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            sample_rate_hertz=24000,  # Hög kvalitet
            speaking_rate=1.0,        # Normal hastighet
            pitch=0.0,               # Normal pitch
            volume_gain_db=0.0       # Normal volym
        )
        
        # Skapa synthesis input
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Generera talet
        print(f"📝 Text ({len(text)} tecken): {text[:100]}...")
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config
        )
        
        # Spara audio content till fil
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
        
        file_size = len(response.audio_content)
        print(f"✅ Google Cloud TTS audio sparad: {output_file} ({file_size} bytes)")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Google Cloud TTS fel: {str(e)}")
        return None

def test_google_cloud_tts_service_account():
    """Testa Google Cloud TTS med service account"""
    
    if not setup_google_credentials():
        return False
    
    try:
        # Skapa TTS client
        client = texttospeech.TextToSpeechClient()
        
        test_text = "Hej och välkommen till Människa Maskin Miljö! Detta är en test av Google Cloud svenska röster med service account."
        
        # Testa svenska röster - inkludera de NYASTE och bästa Chirp3-HD rösterna!
        swedish_voices = [
            # GAMLA (för jämförelse)
            {"name": "sv-SE-Standard-A", "gender": "FEMALE", "desc": "Standard kvinna (gammal)"},
            {"name": "sv-SE-Wavenet-A", "gender": "FEMALE", "desc": "WaveNet kvinna (gammal)"},
            
            # NYA CHIRP3-HD (högsta kvalitet!)
            {"name": "sv-SE-Chirp3-HD-Achernar", "gender": "FEMALE", "desc": "Chirp3-HD kvinna (HÖGSTA kvalitet)"},
            {"name": "sv-SE-Chirp3-HD-Achird", "gender": "MALE", "desc": "Chirp3-HD man (HÖGSTA kvalitet)"},
            {"name": "sv-SE-Chirp3-HD-Gacrux", "gender": "FEMALE", "desc": "Chirp3-HD kvinna (HÖGSTA kvalitet)"},
            {"name": "sv-SE-Chirp3-HD-Fenrir", "gender": "MALE", "desc": "Chirp3-HD man (HÖGSTA kvalitet)"},
            {"name": "sv-SE-Chirp3-HD-Zephyr", "gender": "FEMALE", "desc": "Chirp3-HD kvinna (HÖGSTA kvalitet)"},
            {"name": "sv-SE-Chirp3-HD-Despina", "gender": "FEMALE", "desc": "Chirp3-HD kvinna (HÖGSTA kvalitet)"},
            
            # CHIRP3-HD manliga alternativ
            {"name": "sv-SE-Chirp3-HD-Charon", "gender": "MALE", "desc": "Chirp3-HD man (HÖGSTA kvalitet)"},
            {"name": "sv-SE-Chirp3-HD-Enceladus", "gender": "MALE", "desc": "Chirp3-HD man (HÖGSTA kvalitet)"},
            {"name": "sv-SE-Chirp3-HD-Iapetus", "gender": "MALE", "desc": "Chirp3-HD man (HÖGSTA kvalitet)"},
        ]
        
        print("🎭 Testar Google Cloud svenska röster med service account:")
        
        for voice in swedish_voices:
            try:
                # Konfigurera röst
                voice_config = texttospeech.VoiceSelectionParams(
                    language_code="sv-SE",
                    name=voice["name"],
                    ssml_gender=getattr(texttospeech.SsmlVoiceGender, voice["gender"])
                )
                
                # Konfigurera audio
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    speaking_rate=1.0,
                    pitch=0.0
                )
                
                # Skapa request
                synthesis_input = texttospeech.SynthesisInput(text=test_text)
                
                print(f"  🎤 {voice['name']} ({voice['desc']})...")
                
                # Anropa TTS
                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice_config,
                    audio_config=audio_config
                )
                
                # Spara audio
                filename = f"audio/test_google_sa_{voice['name'].replace('-', '_').lower()}.mp3"
                with open(filename, 'wb') as f:
                    f.write(response.audio_content)
                
                print(f"     ✅ Sparad: {filename} ({len(response.audio_content)} bytes)")
                
            except Exception as e:
                print(f"     ❌ Fel: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Allmänt fel: {e}")
        return False

def create_google_podcast_service_account(segments: List[Dict]) -> str:
    """Skapa podcast med Google Cloud TTS service account"""
    
    if not setup_google_credentials():
        return None
    
    try:
        client = texttospeech.TextToSpeechClient()
        
        # Röstmappning för podcast - använder CHIRP3-HD (högsta kvalitet)
        # UPPDATERAT: Pelle (Iapetus) och Lisa (Gacrux) - de bästa rösterna!
        voice_mapping = {
            'lisa': 'sv-SE-Chirp3-HD-Gacrux',       # BÄSTA kvinna enligt test
            'pelle': 'sv-SE-Chirp3-HD-Iapetus',     # BÄSTA man enligt test 
            'sanna': 'sv-SE-Chirp3-HD-Gacrux',      # Bakåtkompatibilitet
            'george': 'sv-SE-Chirp3-HD-Iapetus',    # Bakåtkompatibilitet
            'female': 'sv-SE-Chirp3-HD-Gacrux',
            'male': 'sv-SE-Chirp3-HD-Iapetus'
        }
        
        print("🎙️ Skapar podcast med Google Cloud TTS (Service Account)...")
        
        audio_files = []
        total_chars = 0
        
        for i, segment in enumerate(segments, 1):
            text = segment.get('text', '')
            voice_name = segment.get('voice', 'sanna').lower()
            
            google_voice = voice_mapping.get(voice_name, 'sv-SE-Chirp3-HD-Gacrux')
            
            # Bestäm kön baserat på röstnamn (Pelle och Lisa)
            if google_voice == 'sv-SE-Chirp3-HD-Gacrux':
                gender = "FEMALE"  # Lisa
            elif google_voice == 'sv-SE-Chirp3-HD-Iapetus':
                gender = "MALE"    # Pelle
            else:
                gender = "FEMALE"  # Default
            
            print(f"🎤 Segment {i}: {voice_name} ({google_voice}) - {text[:50]}...")
            
            try:
                # Konfigurera röst
                voice_config = texttospeech.VoiceSelectionParams(
                    language_code="sv-SE",
                    name=google_voice,
                    ssml_gender=getattr(texttospeech.SsmlVoiceGender, gender)
                )
                
                # Konfigurera audio
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    speaking_rate=1.0,
                    pitch=0.0
                )
                
                # Skapa request
                synthesis_input = texttospeech.SynthesisInput(text=text)
                
                # Anropa TTS
                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice_config,
                    audio_config=audio_config
                )
                
                # Spara temporär fil
                filename = f'audio/temp_google_sa_segment_{i}.mp3'
                with open(filename, 'wb') as f:
                    f.write(response.audio_content)
                
                audio_files.append(filename)
                total_chars += len(text)
                print(f"     ✅ {len(response.audio_content)} bytes")
                
            except Exception as e:
                print(f"     ❌ Fel: {e}")
                continue
        
        if not audio_files:
            print("❌ Inga segment kunde genereras")
            return None
        
        # Kombinera med pydub
        try:
            from pydub import AudioSegment
            
            combined = AudioSegment.empty()
            
            for filename in audio_files:
                audio = AudioSegment.from_mp3(filename)
                combined += audio
                
                # Lägg till 1 sekunds paus mellan segment
                combined += AudioSegment.silent(duration=1000)
                
                # Rensa temp-fil
                os.remove(filename)
            
            output_file = "audio/episode_google_service_account.mp3"
            combined.export(output_file, format="mp3")
            
            duration_minutes = len(combined) / 60000
            cost = total_chars * 0.000004  # $4 per 1M chars
            
            print(f"✅ Google Cloud podcast skapad: {output_file}")
            print(f"🕐 Längd: {duration_minutes:.1f} minuter")
            print(f"📊 Totalt tecken: {total_chars}")
            print(f"💰 Uppskattad kostnad: ~${cost:.6f}")
            print(f"💡 Jämförelse:")
            print(f"   • Google Cloud: ${cost:.6f}")
            print(f"   • OpenAI TTS: ${total_chars * 0.000015:.6f}")
            print(f"   • ElevenLabs: ${total_chars * 0.00018:.3f}")
            
            return output_file
            
        except ImportError:
            print("⚠️ pydub krävs för att kombinera segment")
            return None
        except Exception as e:
            print(f"❌ Fel vid kombinering: {e}")
            return None
            
    except Exception as e:
        print(f"❌ Service account fel: {e}")
        return None

if __name__ == "__main__":
    print("☁️ Google Cloud TTS Service Account Test")
    print("=" * 50)
    
    # Installera Google Cloud bibliotek om det behövs
    try:
        from google.cloud import texttospeech
    except ImportError:
        print("❌ Google Cloud TTS bibliotek saknas!")
        print("Installera med: pip install google-cloud-texttospeech")
        exit(1)
    
    # Testa enskilda röster
    if test_google_cloud_tts_service_account():
        
        # Testa podcast-skapande  
        test_segments = [
            {"text": "Välkommen till Människa Maskin Miljö, vecka test med Google Cloud service account!", "voice": "sanna"},
            {"text": "Google Cloud TTS med WaveNet-röster ger fantastisk kvalitet för svenska podcasts.", "voice": "george"},
            {"text": "Med bara fyra dollar per miljon tecken är detta den mest kostnadseffektiva lösningen.", "voice": "sanna"},
            {"text": "Detta kan definitivt vara den perfekta backup-lösningen när ElevenLabs blir för dyrt.", "voice": "george"}
        ]
        
        create_google_podcast_service_account(test_segments)
    
    else:
        print("\n💡 För att använda Google Cloud TTS:")
        print("1. Ladda ner din service account JSON-fil")
        print("2. Sätt GOOGLE_APPLICATION_CREDENTIALS till filens sökväg")
        print("3. Eller sätt GOOGLE_CLOUD_CREDENTIALS_JSON till JSON-innehållet")

def test_google_cloud_tts():
    """Testa Google Cloud TTS med Gemini API key"""
    
    # Google Cloud TTS kan användas med API key (inte bara OAuth)
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("⚠️ GEMINI_API_KEY saknas")
        return False
    
    # Google Cloud Text-to-Speech endpoint
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    test_text = "Hej och välkommen till Människa Maskin Miljö! Detta är en test av Google Cloud svenska röster."
    
    # Testa svenska röster
    swedish_voices = [
        {"name": "sv-SE-Standard-A", "gender": "FEMALE", "desc": "Standard kvinna"},
        {"name": "sv-SE-Standard-B", "gender": "MALE", "desc": "Standard man"},
        {"name": "sv-SE-Wavenet-A", "gender": "FEMALE", "desc": "WaveNet kvinna (högre kvalitet)"},
        {"name": "sv-SE-Wavenet-B", "gender": "MALE", "desc": "WaveNet man (högre kvalitet)"},
    ]
    
    print("🎭 Testar Google Cloud svenska röster:")
    
    for voice in swedish_voices:
        try:
            data = {
                "input": {"text": test_text},
                "voice": {
                    "languageCode": "sv-SE",
                    "name": voice["name"],
                    "ssmlGender": voice["gender"]
                },
                "audioConfig": {
                    "audioEncoding": "MP3",
                    "speakingRate": 1.0,
                    "pitch": 0.0
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            print(f"  🎤 {voice['name']} ({voice['desc']})...")
            print(f"     Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                audio_content = result.get('audioContent')
                
                if audio_content:
                    audio_bytes = base64.b64decode(audio_content)
                    filename = f"audio/test_google_{voice['name'].replace('-', '_').lower()}.mp3"
                    
                    with open(filename, 'wb') as f:
                        f.write(audio_bytes)
                    
                    print(f"     ✅ Sparad: {filename} ({len(audio_bytes)} bytes)")
                else:
                    print("     ❌ Ingen audio-data")
            else:
                print(f"     ❌ Fel: {response.text}")
                
        except Exception as e:
            print(f"     ❌ Exception: {e}")

def create_google_podcast(segments: List[Dict]) -> str:
    """Skapa podcast med Google Cloud TTS"""
    
    api_key = os.getenv('GEMINI_API_KEY')
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    
    # Röstmappning för podcast - använd de BÄSTA rösterna
    voice_mapping = {
        'sanna': 'sv-SE-Studio-A',        # Kvinna, HÖGSTA kvalitet (Studio)
        'george': 'sv-SE-Studio-B',       # Man, HÖGSTA kvalitet (Studio)
        'female': 'sv-SE-Neural2-A',      # Backup kvinna (Neural2)
        'male': 'sv-SE-Neural2-B'         # Backup man (Neural2)
    }
    
    print("🎙️ Skapar podcast med Google Cloud TTS...")
    
    audio_files = []
    
    for i, segment in enumerate(segments, 1):
        text = segment.get('text', '')
        voice_name = segment.get('voice', 'sanna').lower()
        
        google_voice = voice_mapping.get(voice_name, 'sv-SE-Wavenet-A')
        gender = "FEMALE" if 'A' in google_voice else "MALE"
        
        print(f"🎤 Segment {i}: {voice_name} ({google_voice}) - {text[:50]}...")
        
        try:
            data = {
                "input": {"text": text},
                "voice": {
                    "languageCode": "sv-SE", 
                    "name": google_voice,
                    "ssmlGender": gender
                },
                "audioConfig": {
                    "audioEncoding": "MP3",
                    "speakingRate": 1.0,
                    "pitch": 0.0
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            audio_content = result.get('audioContent')
            
            if audio_content:
                audio_bytes = base64.b64decode(audio_content)
                filename = f'audio/temp_google_segment_{i}.mp3'
                
                with open(filename, 'wb') as f:
                    f.write(audio_bytes)
                
                audio_files.append(filename)
                print(f"     ✅ {len(audio_bytes)} bytes")
            else:
                print(f"     ❌ Ingen audio-data")
                
        except Exception as e:
            print(f"     ❌ Fel: {e}")
            continue
    
    if not audio_files:
        print("❌ Inga segment kunde genereras")
        return None
    
    # Kombinera med pydub
    try:
        from pydub import AudioSegment
        
        combined = AudioSegment.empty()
        
        for filename in audio_files:
            audio = AudioSegment.from_mp3(filename)
            combined += audio
            
            # Lägg till 1 sekunds paus mellan segment
            combined += AudioSegment.silent(duration=1000)
            
            # Rensa temp-fil
            os.remove(filename)
        
        output_file = "audio/episode_google_backup.mp3"
        combined.export(output_file, format="mp3")
        
        duration_minutes = len(combined) / 60000
        total_chars = sum(len(s.get('text', '')) for s in segments)
        cost = total_chars * 0.000004  # $4 per 1M chars
        
        print(f"✅ Google Cloud podcast skapad: {output_file}")
        print(f"🕐 Längd: {duration_minutes:.1f} minuter")
        print(f"💰 Uppskattad kostnad: ~${cost:.4f}")
        
        return output_file
        
    except ImportError:
        print("⚠️ pydub krävs för att kombinera segment")
        return None
    except Exception as e:
        print(f"❌ Fel vid kombinering: {e}")
        return None

if __name__ == "__main__":
    print("☁️ Google Cloud TTS Test")
    print("=" * 30)
    
    if os.getenv('GEMINI_API_KEY'):
        # Testa enskilda röster
        test_google_cloud_tts()
        
        # Testa podcast-skapande  
        test_segments = [
            {"text": "Välkommen till Människa Maskin Miljö, vecka test med Google Cloud!", "voice": "sanna"},
            {"text": "Google Cloud TTS är mycket kostnadseffektivt för svenska podcasts.", "voice": "george"},
            {"text": "Kvaliteten på WaveNet-rösterna är riktigt bra för automatiserade produktioner.", "voice": "sanna"},
            {"text": "Detta kan vara den perfekta backup-lösningen när ElevenLabs är för dyrt.", "voice": "george"}
        ]
        
        create_google_podcast(test_segments)
        
    else:
        print("⚠️ GEMINI_API_KEY saknas - lägg till i .env filen")
