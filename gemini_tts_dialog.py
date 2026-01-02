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
import tempfile
import re

from pydub import AudioSegment

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
        # Normalisera whitespace så vi inte råkar skapa radbrytningar utan talarprefix
        normalized_news = " ".join((news_content or "").split())
        news_segments = self._split_news_for_dialog(normalized_news)
        
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
            segment = " ".join((segment or "").split()).strip()
            if not segment:
                continue
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

    def _utf8_len(self, s: str) -> int:
        return len((s or '').encode('utf-8'))

    def _extract_limit_bytes_from_error(self, error: Exception) -> Optional[int]:
        """Parse API error messages like: "limit of 900 bytes"."""
        try:
            msg = str(error)
            m = re.search(r"limit of (\d+) bytes", msg)
            if not m:
                return None
            value = int(m.group(1))
            return value if value > 0 else None
        except Exception:
            return None

    def _sanitize_dialog_script(self, dialog_script: str) -> str:
        """Best-effort sanitization to avoid known invalid-argument failures."""
        if not dialog_script:
            return ""

        # Remove ASCII control chars except newlines/tabs
        dialog_script = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", dialog_script)

        # Replace ampersand which has historically triggered invalid-argument errors
        dialog_script = dialog_script.replace("&", "och")

        # Normalize whitespace but keep line breaks (speaker turns)
        dialog_script = "\n".join(" ".join(line.split()) for line in dialog_script.splitlines())

        # Ensure each non-empty line starts with a valid speaker alias (Lisa/Pelle).
        # Missing/invalid prefixes have been correlated with "missing turns" in output.
        allowed = {"lisa": "Lisa", "pelle": "Pelle"}
        fixed_lines = []
        last_speaker = "Lisa"
        for raw in dialog_script.splitlines():
            line = (raw or "").strip()
            if not line:
                continue

            m = re.match(r"^\s*([^:\n]{1,24})\s*:\s*(.*)$", line)
            if m:
                who = (m.group(1) or "").strip().lower()
                text = (m.group(2) or "").strip()
                speaker = allowed.get(who)
                if speaker and text:
                    last_speaker = speaker
                    fixed_lines.append(f"{speaker}: {text}")
                    continue

            # If no valid prefix: attach to last speaker.
            fixed_lines.append(f"{last_speaker}: {line}")

        return "\n".join(fixed_lines).strip()

    def _truncate_utf8(self, s: str, max_bytes: int) -> str:
        if self._utf8_len(s) <= max_bytes:
            return s
        # Binärsök gränsen för att undvika att klippa mitt i en multibyte-sekvens
        lo, hi = 0, len(s)
        while lo < hi:
            mid = (lo + hi) // 2
            if self._utf8_len(s[:mid]) <= max_bytes:
                lo = mid + 1
            else:
                hi = mid
        return s[: max(0, lo - 1)]

    def _split_text_by_bytes(self, text: str, max_bytes: int = 3900) -> List[str]:
        """Splitta text så att varje del håller sig under max_bytes (UTF-8).

        Gemini TTS API verkar ha en hård gräns på 4000 bytes för input.text.
        Vi använder lite marginal för säkerhets skull.
        """
        if not text:
            return [""]

        if self._utf8_len(text) <= max_bytes:
            return [text]

        lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
        chunks: List[str] = []
        current: List[str] = []

        def flush():
            if current:
                chunks.append("\n".join(current).strip())
                current.clear()

        for ln in lines:
            candidate = ("\n".join(current + [ln])).strip() if current else ln
            if self._utf8_len(candidate) <= max_bytes:
                current.append(ln)
                continue

            # Om en enskild rad är för lång: splitta grovt på meningar.
            if not current:
                # Behåll ev. talarprefix ("Lisa:"/"Pelle:") för varje del-chunk.
                m = re.match(r"^\s*([^:\n]{1,24}):\s*(.*)$", ln)
                speaker_prefix = None
                body = ln
                if m:
                    speaker_prefix = m.group(1).strip() + ":"
                    body = m.group(2).strip()

                parts: List[str] = []
                buf = ""

                def with_prefix(s: str) -> str:
                    if speaker_prefix:
                        return f"{speaker_prefix} {s}".strip()
                    return s

                for sentence in body.replace('! ', '!|').replace('? ', '?|').replace('. ', '.|').split('|'):
                    sentence = sentence.strip()
                    if not sentence:
                        continue

                    candidate_piece = (buf + " " + sentence).strip() if buf else sentence
                    candidate2 = with_prefix(candidate_piece)

                    if self._utf8_len(candidate2) <= max_bytes:
                        buf = candidate_piece
                    else:
                        if buf:
                            parts.append(with_prefix(buf))
                        # Fallback: hård trunkering om en mening är extremt lång
                        truncated = self._truncate_utf8(sentence, max_bytes - (self._utf8_len(speaker_prefix + " ") if speaker_prefix else 0))
                        buf = truncated

                if buf:
                    parts.append(with_prefix(buf))

                chunks.extend(parts)
            else:
                flush()
                # Efter flush: om raden fortfarande är för lång, splitta den här också.
                if self._utf8_len(ln) <= max_bytes:
                    current.append(ln)
                else:
                    # Reuse the single-line splitting logic by handling as if "current" were empty.
                    m = re.match(r"^\s*([^:\n]{1,24}):\s*(.*)$", ln)
                    speaker_prefix = None
                    body = ln
                    if m:
                        speaker_prefix = m.group(1).strip() + ":"
                        body = m.group(2).strip()

                    parts: List[str] = []
                    buf = ""

                    def with_prefix(s: str) -> str:
                        if speaker_prefix:
                            return f"{speaker_prefix} {s}".strip()
                        return s

                    prefix_bytes = self._utf8_len(speaker_prefix + " ") if speaker_prefix else 0
                    for sentence in body.replace('! ', '!|').replace('? ', '?|').replace('. ', '.|').split('|'):
                        sentence = sentence.strip()
                        if not sentence:
                            continue

                        candidate_piece = (buf + " " + sentence).strip() if buf else sentence
                        candidate2 = with_prefix(candidate_piece)

                        if self._utf8_len(candidate2) <= max_bytes:
                            buf = candidate_piece
                        else:
                            if buf:
                                parts.append(with_prefix(buf))
                            truncated = self._truncate_utf8(sentence, max(50, max_bytes - prefix_bytes))
                            buf = truncated

                    if buf:
                        parts.append(with_prefix(buf))

                    chunks.extend(parts)

        flush()

        # Säkerhetsnät
        safe_chunks = [c for c in chunks if c.strip()]
        return safe_chunks or [self._truncate_utf8(text, max_bytes)]

    def _stitch_mp3_segments(self, mp3_files: List[str], output_file: str) -> None:
        combined: Optional[AudioSegment] = None
        for i, path in enumerate(mp3_files):
            seg = AudioSegment.from_mp3(path)
            if combined is None:
                combined = seg
            else:
                # Lägg en kort paus mellan chunks (undviker att ord flyter ihop)
                combined = combined + AudioSegment.silent(duration=150) + seg

        if combined is None:
            raise RuntimeError("No audio segments to stitch")

        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        combined.export(output_file, format="mp3")
    
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
            # NOTE: Gemini/Vertex endpoints have shown varying byte limits.
            # Keep the prompt small and retry with a smaller chunk limit if the API reports one.
            prompt_max_bytes = int(os.getenv('GEMINI_TTS_PROMPT_MAX_BYTES', '850'))
            chunk_max_bytes_default = int(os.getenv('GEMINI_TTS_MAX_BYTES', '3900'))

            style_prompt = (
                "Swedish news podcast (MMM Senaste Nytt). "
                "Lisa: professional, warm, clear. "
                "Pelle: energetic, curious, explains simply. "
                "Natural Swedish pronunciation and smooth conversational flow."
            )
            style_prompt = self._truncate_utf8(style_prompt.strip(), prompt_max_bytes)

            dialog_script = self._sanitize_dialog_script(dialog_script)
            if not dialog_script:
                logger.warning("[GEMINI-TTS] Tomt dialog-script efter sanering")
                return False

            def build_chunks(max_bytes: int) -> List[str]:
                return self._split_text_by_bytes(dialog_script, max_bytes=max_bytes)

            # Attempt 1: default chunk size
            attempt_limits = [chunk_max_bytes_default]

            def run_synthesis_for_chunks(chunks_to_use: List[str]) -> None:
                if len(chunks_to_use) == 1:
                    synthesis_input = texttospeech.SynthesisInput(
                        text=chunks_to_use[0],
                        prompt=style_prompt
                    )

                    logger.info("[GEMINI-TTS] Genererar dialog mellan Lisa och Pelle...")
                    response = self.client.synthesize_speech(
                        input=synthesis_input,
                        voice=voice,
                        audio_config=audio_config
                    )

                    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
                    with open(output_file, "wb") as out:
                        out.write(response.audio_content)

                    logger.info(f"[GEMINI-TTS] Dialog sparad: {output_file}")
                    return

                tmp_files: List[str] = []
                try:
                    logger.info(
                        f"[GEMINI-TTS] Dialogen är {self._utf8_len(dialog_script)} bytes; "
                        f"splittar i {len(chunks_to_use)} chunks (max_bytes={max(self._utf8_len(c) for c in chunks_to_use)})"
                    )

                    for idx, chunk in enumerate(chunks_to_use, start=1):
                        synthesis_input = texttospeech.SynthesisInput(
                            text=chunk,
                            prompt=style_prompt
                        )

                        logger.info(f"[GEMINI-TTS] Genererar chunk {idx}/{len(chunks_to_use)} ({self._utf8_len(chunk)} bytes)")
                        response = self.client.synthesize_speech(
                            input=synthesis_input,
                            voice=voice,
                            audio_config=audio_config
                        )

                        fd, tmp_path = tempfile.mkstemp(prefix=f"gemini_tts_{idx}_", suffix=".mp3")
                        os.close(fd)
                        with open(tmp_path, "wb") as out:
                            out.write(response.audio_content)
                        tmp_files.append(tmp_path)

                    self._stitch_mp3_segments(tmp_files, output_file)
                    logger.info(f"[GEMINI-TTS] Dialog (chunkad) sparad: {output_file}")
                finally:
                    for p in tmp_files:
                        try:
                            os.remove(p)
                        except Exception:
                            pass

            # We build voice/audio_config before attempting synthesis (existing code below)
            
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

            # Attempt synthesis; if the API reports a lower byte-limit, retry with that.
            last_error: Optional[Exception] = None
            for attempt_index, max_bytes in enumerate(attempt_limits, start=1):
                try:
                    chunks = build_chunks(max_bytes=max_bytes)
                    logger.info(
                        f"[GEMINI-TTS] Försök {attempt_index}/{len(attempt_limits)} "
                        f"(chunk_max_bytes={max_bytes}, prompt_bytes={self._utf8_len(style_prompt)})"
                    )
                    run_synthesis_for_chunks(chunks)
                    return True
                except Exception as e:
                    last_error = e
                    limit = self._extract_limit_bytes_from_error(e)
                    logger.warning(f"[GEMINI-TTS] Försök {attempt_index} misslyckades: {e}")

                    # If the API tells us the real limit, retry once with a safe margin.
                    if limit is not None and len(attempt_limits) == 1:
                        safe = max(200, limit - 50)
                        attempt_limits.append(safe)
                        logger.info(f"[GEMINI-TTS] Upptäckte byte-limit {limit}; retry med max_bytes={safe}")
                        continue
                    break

            raise last_error if last_error is not None else RuntimeError("Gemini TTS failed")
            
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
            prompt_max_bytes = int(os.getenv('GEMINI_TTS_PROMPT_MAX_BYTES', '850'))
            chunk_max_bytes_default = int(os.getenv('GEMINI_TTS_MAX_BYTES', '3900'))

            def sanitize_turn_text(text: str) -> str:
                # Reuse the same sanitization logic as freeform, but keep it single-line.
                return self._sanitize_dialog_script(text).replace("\n", " ")

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
                    text=sanitize_turn_text("Men först, hur ser vädret ut idag?")
                ),
                texttospeech.MultiSpeakerMarkup.Turn(
                    speaker_alias="Pelle",
                    text=sanitize_turn_text(f"[informative] {weather_info}")
                )
            ])
            
            # Nyheter
            for i, segment in enumerate(news_segments):
                speaker = "Lisa" if i % 2 == 0 else "Pelle"
                emotion_tag = f"[{segment.get('emotion', 'neutral')}]" if segment.get('emotion') else ""
                
                turns.append(
                    texttospeech.MultiSpeakerMarkup.Turn(
                        speaker_alias=speaker,
                        text=sanitize_turn_text(f"{emotion_tag} {segment['text']}")
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
            style_prompt = (
                "Swedish news podcast (MMM Senaste Nytt). "
                "Lisa: professional, warm, clear. "
                "Pelle: energetic, curious, explains simply. "
                "Natural Swedish pronunciation and smooth conversational flow."
            )
            style_prompt = self._truncate_utf8(style_prompt.strip(), prompt_max_bytes)

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

            def normalize_turns(max_bytes: int) -> List[texttospeech.MultiSpeakerMarkup.Turn]:
                """Ensure no single turn exceeds max_bytes by splitting long turns."""
                normalized: List[texttospeech.MultiSpeakerMarkup.Turn] = []
                for t in turns:
                    speaker_alias = getattr(t, 'speaker_alias', None)
                    txt = getattr(t, 'text', '') or ''
                    if self._utf8_len(txt) <= max_bytes:
                        normalized.append(t)
                        continue

                    # Split very long turn text into multiple turns with same speaker
                    parts = self._split_text_by_bytes(txt, max_bytes=max(200, max_bytes - 10))
                    for part in parts:
                        normalized.append(
                            texttospeech.MultiSpeakerMarkup.Turn(
                                speaker_alias=speaker_alias,
                                text=part
                            )
                        )
                return normalized

            def chunk_turns(max_bytes: int) -> List[List[texttospeech.MultiSpeakerMarkup.Turn]]:
                normalized = normalize_turns(max_bytes=max_bytes)
                chunks: List[List[texttospeech.MultiSpeakerMarkup.Turn]] = []
                current: List[texttospeech.MultiSpeakerMarkup.Turn] = []
                current_bytes = 0

                for t in normalized:
                    t_bytes = self._utf8_len(getattr(t, 'text', '')) + 1
                    if current and current_bytes + t_bytes > max_bytes:
                        chunks.append(current)
                        current = []
                        current_bytes = 0
                    current.append(t)
                    current_bytes += t_bytes

                if current:
                    chunks.append(current)
                return chunks

            def run_synthesis(turn_chunks: List[List[texttospeech.MultiSpeakerMarkup.Turn]]) -> None:
                if len(turn_chunks) == 1:
                    synthesis_input = texttospeech.SynthesisInput(
                        multi_speaker_markup=texttospeech.MultiSpeakerMarkup(turns=turn_chunks[0]),
                        prompt=style_prompt
                    )
                    response = self.client.synthesize_speech(
                        input=synthesis_input,
                        voice=voice,
                        audio_config=audio_config
                    )
                    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
                    with open(output_file, "wb") as out:
                        out.write(response.audio_content)
                    logger.info(f"[GEMINI-TTS] Strukturerad dialog sparad: {output_file}")
                    return

                logger.info(f"[GEMINI-TTS] Strukturerad dialog kräver {len(turn_chunks)} chunks")
                tmp_files: List[str] = []
                try:
                    for idx, chunk_turns in enumerate(turn_chunks, start=1):
                        synthesis_input = texttospeech.SynthesisInput(
                            multi_speaker_markup=texttospeech.MultiSpeakerMarkup(turns=chunk_turns),
                            prompt=style_prompt
                        )
                        chunk_bytes = sum(self._utf8_len(getattr(t, 'text', '')) + 1 for t in chunk_turns)
                        logger.info(f"[GEMINI-TTS] Genererar structured chunk {idx}/{len(turn_chunks)} (~{chunk_bytes} bytes)")
                        response = self.client.synthesize_speech(
                            input=synthesis_input,
                            voice=voice,
                            audio_config=audio_config
                        )
                        fd, tmp_path = tempfile.mkstemp(prefix=f"gemini_tts_struct_{idx}_", suffix=".mp3")
                        os.close(fd)
                        with open(tmp_path, "wb") as out:
                            out.write(response.audio_content)
                        tmp_files.append(tmp_path)

                    self._stitch_mp3_segments(tmp_files, output_file)
                    logger.info(f"[GEMINI-TTS] Strukturerad dialog (chunkad) sparad: {output_file}")
                finally:
                    for p in tmp_files:
                        try:
                            os.remove(p)
                        except Exception:
                            pass

            last_error: Optional[Exception] = None
            attempt_limits = [chunk_max_bytes_default]
            for attempt_index, max_bytes in enumerate(attempt_limits, start=1):
                try:
                    turn_chunks = chunk_turns(max_bytes=max_bytes)
                    logger.info(
                        f"[GEMINI-TTS] Structured försök {attempt_index}/{len(attempt_limits)} "
                        f"(chunk_max_bytes={max_bytes}, prompt_bytes={self._utf8_len(style_prompt)})"
                    )
                    run_synthesis(turn_chunks)
                    return True
                except Exception as e:
                    last_error = e
                    limit = self._extract_limit_bytes_from_error(e)
                    logger.warning(f"[GEMINI-TTS] Structured försök {attempt_index} misslyckades: {e}")
                    if limit is not None and len(attempt_limits) == 1:
                        safe = max(200, limit - 50)
                        attempt_limits.append(safe)
                        logger.info(f"[GEMINI-TTS] Upptäckte byte-limit {limit}; retry med chunk_max_bytes={safe}")
                        continue
                    break

            raise last_error if last_error is not None else RuntimeError("Gemini structured TTS failed")
            
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