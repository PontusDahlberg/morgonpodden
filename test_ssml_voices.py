#!/usr/bin/env python3
"""
Testa svenska röster som stöder SSML
"""

import os
from google.cloud import texttospeech

def test_swedish_ssml_voices():
    """Testar svenska röster med SSML-stöd"""
    
    # Sätt upp credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-service-account.json'
    
    try:
        client = texttospeech.TextToSpeechClient()
        
        # Svenska röster som STÖDER SSML (baserat på Google-dokumentation)
        ssml_voices = [
            # Standard-röster (grundläggande SSML)
            {"name": "sv-SE-Standard-A", "gender": "FEMALE", "type": "Standard"},
            {"name": "sv-SE-Standard-B", "gender": "FEMALE", "type": "Standard"}, 
            {"name": "sv-SE-Standard-C", "gender": "FEMALE", "type": "Standard"},
            {"name": "sv-SE-Standard-D", "gender": "MALE", "type": "Standard"},
            {"name": "sv-SE-Standard-E", "gender": "MALE", "type": "Standard"},
            
            # WaveNet-röster (bättre kvalitet + SSML)
            {"name": "sv-SE-Wavenet-A", "gender": "FEMALE", "type": "WaveNet"},
            {"name": "sv-SE-Wavenet-B", "gender": "FEMALE", "type": "WaveNet"},
            {"name": "sv-SE-Wavenet-C", "gender": "MALE", "type": "WaveNet"},
            {"name": "sv-SE-Wavenet-D", "gender": "FEMALE", "type": "WaveNet"},
            {"name": "sv-SE-Wavenet-E", "gender": "MALE", "type": "WaveNet"},
        ]
        
        print("🧪 TESTAR: Svenska röster med SSML-stöd")
        print("=" * 50)
        
        # Test-text med SSML för känslomässig styrning
        test_texts = [
            {
                "name": "Normal",
                "ssml": """<speak>
                    Hej och välkommen till dagens avsnitt av MMM Senaste Nytt!
                </speak>"""
            },
            {
                "name": "Betonad + Långsam",
                "ssml": """<speak>
                    <prosody rate="slow" pitch="+2st">
                        <emphasis level="strong">Fantastiska nyheter</emphasis> från teknikvärlden idag!
                    </prosody>
                </speak>"""
            },
            {
                "name": "Glad/Exalterad stil",
                "ssml": """<speak>
                    <prosody rate="medium" pitch="+5st" volume="loud">
                        Det här är verkligen <emphasis level="strong">spännande</emphasis>!
                        <break time="0.5s"/>
                        Ni kommer aldrig att gissa vad som hänt!
                    </prosody>
                </speak>"""
            },
            {
                "name": "Seriös/Bekymrad stil", 
                "ssml": """<speak>
                    <prosody rate="slow" pitch="-2st" volume="medium">
                        Detta är <emphasis level="moderate">verkligen bekymrande</emphasis>.
                        <break time="0.8s"/>
                        Vi måste ta det här på allvar.
                    </prosody>
                </speak>"""
            }
        ]
        
        # Testa bara de bästa WaveNet-rösterna
        best_voices = [
            {"name": "sv-SE-Wavenet-A", "gender": "FEMALE", "type": "WaveNet"},
            {"name": "sv-SE-Wavenet-C", "gender": "MALE", "type": "WaveNet"},
        ]
        
        for voice_info in best_voices:
            voice_name = voice_info["name"]
            gender = getattr(texttospeech.SsmlVoiceGender, voice_info["gender"])
            
            print(f"\n🎤 {voice_name} ({voice_info['gender']}):")
            
            for i, test_text in enumerate(test_texts):
                try:
                    # Konfigurera röst
                    voice = texttospeech.VoiceSelectionParams(
                        language_code="sv-SE",
                        name=voice_name,
                        ssml_gender=gender,
                    )
                    
                    # Audio konfiguration
                    audio_config = texttospeech.AudioConfig(
                        audio_encoding=texttospeech.AudioEncoding.MP3,
                        sample_rate_hertz=24000
                    )
                    
                    # Använd SSML input istället för text
                    synthesis_input = texttospeech.SynthesisInput(ssml=test_text["ssml"])
                    
                    # Generera tal
                    response = client.synthesize_speech(
                        input=synthesis_input,
                        voice=voice,
                        audio_config=audio_config
                    )
                    
                    # Spara fil
                    safe_voice = voice_name.lower().replace("-", "_")
                    filename = f"audio/ssml_test_{safe_voice}_{i+1}_{test_text['name'].lower().replace(' ', '_').replace('/', '_')}.mp3"
                    
                    with open(filename, "wb") as out:
                        out.write(response.audio_content)
                    
                    file_size = len(response.audio_content)
                    print(f"   ✅ {test_text['name']}: {filename} ({file_size} bytes)")
                    
                except Exception as e:
                    print(f"   ❌ {test_text['name']}: {str(e)}")
        
        print(f"\n🎧 RESULTAT:")
        print("   • Test-filer skapade i audio/ mappen")
        print("   • Jämför kvalitet och känslomässig styrning")
        print("   • Är WaveNet + SSML tillräckligt bra som ersättning?")
        print("\n💰 KOSTNAD:")
        print("   • WaveNet: $0.016 per 1000 tecken (4x dyrare än Chirp3-HD)")
        print("   • Fortfarande 11x billigare än ElevenLabs!")
        
        return True
        
    except Exception as e:
        print(f"❌ Fel vid SSML-test: {str(e)}")
        return False

if __name__ == "__main__":
    test_swedish_ssml_voices()