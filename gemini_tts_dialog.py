#!/usr/bin/env python3
"""
Gemini TTS Integration för MMM Senaste Nytt
Multi-speaker dialog mellan Lisa och Pelle med natural language prompts
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
from google.cloud import texttospeech
import json

logger = logging.getLogger(__name__)

class GeminiTTSDialogGenerator:
    """Generera naturlig dialog mellan Lisa och Pelle med Gemini TTS"""
    
    def __init__(self):
        # Sätt upp credentials
        cred_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'google-cloud-service-account.json')
        if os.path.exists(cred_file):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.abspath(cred_file)
            logger.info(f"[GEMINI-TTS] Använder credentials: {cred_file}")
        
        self.client = texttospeech.TextToSpeechClient()
        
        # Svenska Gemini TTS röster för Lisa och Pelle
        self.voices = {
            "Lisa": {
                "speaker_id": "Gacrux",  # Kvinnlig röst (samma som vi använder nu)
                "personality": "professionell och vänlig nyhetspresentatör",
                "style": "klar och engagerad, med ett vänligt men auktoritativt tonfall"
            },
            "Pelle": {
                "speaker_id": "Iapetus",  # Manlig röst (samma som vi använder nu)  
                "personality": "entusiastisk teknikexpert och medpresentatör",
                "style": "energisk och nyfiken, med fokus på att förklara komplexa ämnen enkelt"
            }
        }
    
    def create_dialog_script(self, news_content: str, weather_info: str) -> str:
        """
        Skapa dialog-script för Lisa och Pelle
        
        Args:
            news_content: Processerat nyhetsinnehåll
            weather_info: Väderinformation
            
        Returns:
            Dialog-script i Gemini TTS format
        """
        # Dela upp nyheterna i segment för dialog
        news_segments = self._split_news_for_dialog(news_content)
        
        # Bygg dialog
        dialog_parts = []
        
        # Intro
        dialog_parts.append(f"Lisa: Hej och välkomna till MMM Senaste Nytt! Jag är Lisa.")
        dialog_parts.append(f"Pelle: [enthusiastic] Och jag är Pelle! Vi har spännande nyheter idag inom AI, teknik och klimat.")
        
        # Väder
        dialog_parts.append(f"Lisa: [friendly] Men först, hur ser vädret ut idag, Pelle?")
        dialog_parts.append(f"Pelle: [informative] {weather_info}")
        
        # Nyheter
        for i, segment in enumerate(news_segments):
            if i % 2 == 0:  # Lisa tar udda segment
                dialog_parts.append(f"Lisa: [engaging] {segment}")
            else:  # Pelle tar jämna segment
                dialog_parts.append(f"Pelle: [curious] {segment}")
        
        # Outro
        dialog_parts.append(f"Lisa: [warm] Det var allt för idag från MMM Senaste Nytt.")
        dialog_parts.append(f"Pelle: [upbeat] Ha en fantastisk dag, och vi hörs imorgon!")
        
        return "\n".join(dialog_parts)
    
    def _split_news_for_dialog(self, news_content: str) -> List[str]:
        """Dela upp nyheter i naturliga dialogsegment"""
        # Enkel implementering - dela på meningar och gruppera
        sentences = news_content.split('. ')
        segments = []
        
        current_segment = ""
        for sentence in sentences:
            if len(current_segment + sentence) < 200:  # Max ~200 tecken per segment
                current_segment += sentence + ". "
            else:
                if current_segment:
                    segments.append(current_segment.strip())
                current_segment = sentence + ". "
        
        if current_segment:
            segments.append(current_segment.strip())
        
        return segments
    
    def synthesize_dialog_freeform(self, dialog_script: str, output_file: str) -> bool:
        """
        Skapa audio från dialog-script med freeform text input
        
        Args:
            dialog_script: Dialog mellan Lisa och Pelle
            output_file: Utdatafil för audio
            
        Returns:
            True om framgångsrik
        """
        try:
            # Natural language prompt för hela dialogen
            style_prompt = """
            You are creating a Swedish news podcast called 'MMM Senaste Nytt'. 
            Lisa is a professional, friendly news presenter with a clear and engaging tone.
            Pelle is an enthusiastic tech expert and co-presenter, energetic and curious.
            
            Present the news in a conversational, professional but accessible way.
            Use natural Swedish pronunciation and intonation.
            Make the conversation flow naturally between the two speakers.
            """
            
            # Konfigurera synthesis input
            synthesis_input = texttospeech.SynthesisInput(
                text=dialog_script,
                prompt=style_prompt
            )
            
            # Konfigurera multi-speaker voice
            multi_speaker_voice_config = texttospeech.MultiSpeakerVoiceConfig(
                speaker_voice_configs=[
                    texttospeech.MultispeakerPrebuiltVoice(
                        speaker_alias="Lisa",
                        speaker_id=self.voices["Lisa"]["speaker_id"]
                    ),
                    texttospeech.MultispeakerPrebuiltVoice(
                        speaker_alias="Pelle", 
                        speaker_id=self.voices["Pelle"]["speaker_id"]
                    )
                ]
            )
            
            # Konfigurera röst
            voice = texttospeech.VoiceSelectionParams(
                language_code="sv-SE",
                model_name="gemini-2.5-pro-tts",  # Pro för bästa kvalitet
                multi_speaker_voice_config=multi_speaker_voice_config
            )
            
            # Audio-konfiguration
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                sample_rate_hertz=24000
            )
            
            logger.info("[GEMINI-TTS] Genererar dialog mellan Lisa och Pelle...")
            
            # Syntetisera
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Spara audio
            with open(output_file, "wb") as out:
                out.write(response.audio_content)
            
            logger.info(f"[GEMINI-TTS] Dialog sparad: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"[GEMINI-TTS] Fel vid dialog-generering: {e}")
            return False
    
    def synthesize_dialog_structured(self, news_segments: List[Dict], 
                                   weather_info: str, output_file: str) -> bool:
        """
        Skapa audio med strukturerad dialog input
        
        Args:
            news_segments: Lista med nyhetssegment och emotioner
            weather_info: Väderinformation  
            output_file: Utdatafil
            
        Returns:
            True om framgångsrik
        """
        try:
            # Bygg strukturerade turns
            turns = []
            
            # Intro turns
            turns.extend([
                texttospeech.MultiSpeakerMarkup.Turn(
                    speaker_alias="Lisa",
                    text="Hej och välkomna till MMM Senaste Nytt! Jag är Lisa."
                ),
                texttospeech.MultiSpeakerMarkup.Turn(
                    speaker_alias="Pelle", 
                    text="[enthusiastic] Och jag är Pelle! Vi har spännande nyheter idag."
                )
            ])
            
            # Väder
            turns.extend([
                texttospeech.MultiSpeakerMarkup.Turn(
                    speaker_alias="Lisa",
                    text="Men först, hur ser vädret ut idag?"
                ),
                texttospeech.MultiSpeakerMarkup.Turn(
                    speaker_alias="Pelle",
                    text=f"[informative] {weather_info}"
                )
            ])
            
            # Nyheter
            for i, segment in enumerate(news_segments):
                speaker = "Lisa" if i % 2 == 0 else "Pelle"
                emotion_tag = f"[{segment.get('emotion', 'neutral')}]" if segment.get('emotion') else ""
                
                turns.append(
                    texttospeech.MultiSpeakerMarkup.Turn(
                        speaker_alias=speaker,
                        text=f"{emotion_tag} {segment['text']}"
                    )
                )
            
            # Outro
            turns.extend([
                texttospeech.MultiSpeakerMarkup.Turn(
                    speaker_alias="Lisa",
                    text="[warm] Det var allt för idag från MMM Senaste Nytt."
                ),
                texttospeech.MultiSpeakerMarkup.Turn(
                    speaker_alias="Pelle",
                    text="[upbeat] Ha en fantastisk dag, och vi hörs imorgon!"
                )
            ])
            
            # Style prompt
            style_prompt = """
            Create a Swedish news podcast with natural conversation flow.
            Lisa speaks with professional authority but warmth.
            Pelle brings enthusiasm and explains complex topics simply.
            Use proper Swedish pronunciation and natural intonation.
            """
            
            # Synthesis input
            synthesis_input = texttospeech.SynthesisInput(
                multi_speaker_markup=texttospeech.MultiSpeakerMarkup(turns=turns),
                prompt=style_prompt
            )
            
            # Voice config (samma som freeform)
            multi_speaker_voice_config = texttospeech.MultiSpeakerVoiceConfig(
                speaker_voice_configs=[
                    texttospeech.MultispeakerPrebuiltVoice(
                        speaker_alias="Lisa",
                        speaker_id=self.voices["Lisa"]["speaker_id"]
                    ),
                    texttospeech.MultispeakerPrebuiltVoice(
                        speaker_alias="Pelle",
                        speaker_id=self.voices["Pelle"]["speaker_id"]
                    )
                ]
            )
            
            voice = texttospeech.VoiceSelectionParams(
                language_code="sv-SE",
                model_name="gemini-2.5-pro-tts",
                multi_speaker_voice_config=multi_speaker_voice_config
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                sample_rate_hertz=24000
            )
            
            logger.info("[GEMINI-TTS] Genererar strukturerad dialog...")
            
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice, 
                audio_config=audio_config
            )
            
            with open(output_file, "wb") as out:
                out.write(response.audio_content)
            
            logger.info(f"[GEMINI-TTS] Strukturerad dialog sparad: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"[GEMINI-TTS] Fel vid strukturerad dialog: {e}")
            return False

def test_gemini_tts():
    """Test Gemini TTS dialog generation"""
    generator = GeminiTTSDialogGenerator()
    
    # Test data
    test_news = """
    Artificiell intelligens utvecklas i rekordfart. 
    OpenAI har lanserat nya verktyg för utvecklare.
    Klimatförändringarna påverkar vädermönster globalt.
    Svensk forskning leder inom hållbar teknik.
    """
    
    test_weather = "I Göteborg är det växlande molnighet med 12 grader och måttliga vindar."
    
    # Test freeform dialog
    print("🎭 Testar Gemini TTS multi-speaker dialog...")
    
    dialog_script = generator.create_dialog_script(test_news, test_weather)
    print(f"📝 Dialog script:\n{dialog_script}")
    
    success = generator.synthesize_dialog_freeform(
        dialog_script, 
        "test_gemini_dialog.mp3"
    )
    
    print(f"✅ Gemini TTS test: {'Framgångsrik' if success else 'Misslyckades'}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_gemini_tts()