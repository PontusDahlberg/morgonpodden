#!/usr/bin/env python3
"""
Kvalitetstest för Google Cloud Chirp3-HD svenska röster
Skapar testfiler för manuell bedömning av röstkvalitet
"""

import os
from google.cloud import texttospeech

def test_chirp3_voices():
    """Testar olika Chirp3-HD röster för kvalitetsjämförelse"""
    
    # Sätt upp service account credentials
    credentials_path = "google-cloud-service-account.json"
    if os.path.exists(credentials_path):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        print(f"✅ Använder credentials från: {credentials_path}")
    else:
        print("❌ Kunde inte hitta service account fil")
        return False
    
    try:
        client = texttospeech.TextToSpeechClient()
        
        # Längre testtext som låter mer som en podcast
        test_text = """
        Välkommen till dagens avsnitt av Människa Maskin Miljö! 
        Idag ska vi prata om den senaste utvecklingen inom artificiell intelligens 
        och hur den påverkar vårt dagliga liv. 
        Vi börjar med att titta på de nya språkmodellerna som har släppts den här månaden,
        och sedan diskuterar vi vilka etiska frågor som dyker upp när AI blir allt mer avancerad.
        Det här är verkligen spännande tider vi lever i!
        """
        
        # De bästa Chirp3-HD svenska rösterna (baserat på listan)
        best_voices = [
            {"name": "sv-SE-Chirp3-HD-Achernar", "gender": "FEMALE", "desc": "Achernar (kvinna)"},
            {"name": "sv-SE-Chirp3-HD-Achird", "gender": "MALE", "desc": "Achird (man)"},
            {"name": "sv-SE-Chirp3-HD-Gacrux", "gender": "FEMALE", "desc": "Gacrux (kvinna)"},
            {"name": "sv-SE-Chirp3-HD-Fenrir", "gender": "MALE", "desc": "Fenrir (man)"},
            {"name": "sv-SE-Chirp3-HD-Zephyr", "gender": "FEMALE", "desc": "Zephyr (kvinna)"},
            {"name": "sv-SE-Chirp3-HD-Despina", "gender": "FEMALE", "desc": "Despina (kvinna)"},
            {"name": "sv-SE-Chirp3-HD-Iapetus", "gender": "MALE", "desc": "Iapetus (man)"},
            {"name": "sv-SE-Chirp3-HD-Charon", "gender": "MALE", "desc": "Charon (man)"},
        ]
        
        print(f"\n🎤 Testar {len(best_voices)} Chirp3-HD röster med längre podcasttext:")
        print("=" * 70)
        
        for voice_info in best_voices:
            voice_name = voice_info["name"]
            gender = getattr(texttospeech.SsmlVoiceGender, voice_info["gender"])
            desc = voice_info["desc"]
            
            print(f"🎭 {desc}...")
            
            try:
                # Konfigurera röst
                voice = texttospeech.VoiceSelectionParams(
                    language_code="sv-SE",
                    name=voice_name,
                    ssml_gender=gender,
                )
                
                # Audio konfiguration (högsta kvalitet)
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    sample_rate_hertz=24000,
                    speaking_rate=1.0,
                    pitch=0.0,
                    volume_gain_db=0.0
                )
                
                # Text input
                synthesis_input = texttospeech.SynthesisInput(text=test_text)
                
                # Generera tal
                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )
                
                # Spara till fil
                safe_name = voice_name.lower().replace("-", "_")
                filename = f"audio/chirp3_quality_{safe_name}.mp3"
                
                with open(filename, "wb") as out:
                    out.write(response.audio_content)
                
                file_size = len(response.audio_content)
                print(f"   ✅ {filename} ({file_size} bytes)")
                
            except Exception as e:
                print(f"   ❌ Fel: {str(e)}")
        
        print("\n💡 REKOMMENDATION:")
        print("Lyssna på filerna i audio/ mappen och jämför kvaliteten")
        print("Välj den röst som låter mest naturlig för podcast-användning")
        print("\nFilerna börjar med 'chirp3_quality_*'")
        
        return True
        
    except Exception as e:
        print(f"❌ Fel vid setup: {str(e)}")
        return False

if __name__ == "__main__":
    print("🎙️ Google Cloud Chirp3-HD Kvalitetstest")
    print("=" * 50)
    test_chirp3_voices()
