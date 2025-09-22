#!/usr/bin/env python3
"""
Intelligent musikmixer för Människa Maskin Miljö podcast
Väljer musik baserat på emotion och mixar med tal
"""

import json
import os
import logging
from typing import Dict, List, Optional
from pydub import AudioSegment
from pydub.effects import normalize
import random

logger = logging.getLogger(__name__)

class MusicMixer:
    def __init__(self, music_library_path: str = "music_library.json"):
        self.music_library_path = music_library_path
        self.music_library = self.load_music_library()
        
    def load_music_library(self) -> Dict:
        """Ladda musik-bibliotek från JSON"""
        try:
            with open(self.music_library_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Music library not found: {self.music_library_path}")
            return {"tracks": {}, "moods": {}}
    
    def get_music_for_emotion(self, emotion: str, category: str = "news") -> Optional[str]:
        """
        Hitta lämplig musik för en given emotion
        
        Args:
            emotion: exciting, serious, friendly, professional
            category: intro, news, tech, transition, outro
        
        Returns:
            Sökväg till musikfil eller None
        """
        # Förbättrad mappa våra emotions till musik-moods
        emotion_to_mood = {
            'exciting': ['upbeat', 'playful', 'mysterious'],  # Mer energisk musik
            'serious': ['serious', 'dramatic'],  # Behåll allvarlig för viktiga nyheter
            'friendly': ['playful', 'calm', 'upbeat'],  # Mer positiv musik
            'professional': ['calm', 'playful']  # Mindre dystert för professionellt innehåll
        }
        
        # Speciella regler för bryggmusik - undvik för dyster musik
        if category == "transition":
            # För bryggkor, prioritera ljusare toner
            emotion_to_mood = {
                'exciting': ['upbeat', 'playful'],  # Bara energisk musik
                'serious': ['calm', 'serious'],  # Undvik dramatisk för bryggkor
                'friendly': ['playful', 'upbeat'],  # Bara glad musik
                'professional': ['calm', 'playful']  # Behåll ljus ton
            }
        
        target_moods = emotion_to_mood.get(emotion, ['calm', 'playful'])
        
        # Hitta matchande spår - prioritera rätt kategori först
        matching_tracks = []
        for track_id, track in self.music_library.get("tracks", {}).items():
            # Kolla om kategori matchar
            if category in track.get("categories", []):
                # Kolla om mood matchar
                track_moods = track.get("moods", [])
                if any(mood in track_moods for mood in target_moods):
                    matching_tracks.append(track)
        
        # Om ingen matchning på kategori, leta bredare men undvik dyster musik
        if not matching_tracks:
            for track_id, track in self.music_library.get("tracks", {}).items():
                track_moods = track.get("moods", [])
                # Undvik dramatic och mysterious för bryggkor
                if category == "transition" and ('dramatic' in track_moods or 'mysterious' in track_moods):
                    continue
                if any(mood in track_moods for mood in target_moods):
                    matching_tracks.append(track)
        
        if matching_tracks:
            # Välj slumpmässigt från matchande spår
            selected_track = random.choice(matching_tracks)
            logger.info(f"🎵 Selected {emotion} music: {selected_track.get('title', 'Unknown')} ({', '.join(selected_track.get('moods', []))})")
            return selected_track.get("path")
        
        logger.warning(f"No suitable music found for emotion: {emotion}, category: {category}")
        return None
    
    def mix_speech_with_music(self, speech_file: str, music_file: str, output_file: str, 
                            music_volume: float = -20, fade_in: int = 1000, fade_out: int = 1000) -> bool:
        """
        Mixa tal med bakgrundsmusik
        
        Args:
            speech_file: Sökväg till tal-audio
            music_file: Sökväg till musik
            output_file: Utdata-fil
            music_volume: Musik-volym i dB (negativ för lägre)
            fade_in: Fade-in tid för musik (ms)
            fade_out: Fade-out tid för musik (ms)
        
        Returns:
            True om framgångsrik, False annars
        """
        try:
            # Ladda audio-filer
            speech = AudioSegment.from_file(speech_file)
            music = AudioSegment.from_file(music_file)
            
            # Justera musik-volym
            music = music + music_volume
            
            # Loopa musik om den är kortare än talet
            while len(music) < len(speech):
                music = music + music
            
            # Beskär musik till samma längd som talet
            music = music[:len(speech)]
            
            # Lägg till fade-in och fade-out
            music = music.fade_in(fade_in).fade_out(fade_out)
            
            # Mixa ihop
            mixed = speech.overlay(music)
            
            # Normalisera och exportera
            mixed = normalize(mixed)
            mixed.export(output_file, format="mp3")
            
            logger.info(f"✅ Mixed audio exported: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error mixing audio: {e}")
            return False
    
    def create_podcast_with_musical_bridges(self, segments: List[Dict], output_file: str) -> bool:
        """
        Skapa podcast med musik som bryggkor mellan inslag, inte konstant bakgrund
        
        Args:
            segments: Lista med {'speech_file': path, 'emotion': str, 'duration': int}
            output_file: Final utdata-fil
        
        Returns:
            True om framgångsrik
        """
        try:
            combined = AudioSegment.empty()
            
            for i, segment in enumerate(segments):
                speech_file = segment['speech_file']
                emotion = segment['emotion']
                
                # Ladda tal-audio
                if not os.path.exists(speech_file):
                    logger.warning(f"Speech file not found: {speech_file}")
                    continue
                    
                speech = AudioSegment.from_file(speech_file)
                
                # För första segmentet: kort intro-musik (3-4 sekunder)
                if i == 0:
                    intro_music = self.get_music_for_emotion("professional", "intro")
                    if intro_music and os.path.exists(intro_music):
                        intro = AudioSegment.from_file(intro_music)[:4000]  # 4 sekunder
                        intro = intro.fade_out(1000) - 15  # Fade ut, lägre volym
                        combined += intro
                
                # Lägg till tal-segmentet
                combined += speech
                
                # Mellan segment (inte efter sista): kort musical bridge
                if i < len(segments) - 1:
                    next_emotion = segments[i + 1]['emotion']
                    
                    # Välj bridge-musik baserat på nästa segments emotion
                    bridge_music = self.get_music_for_emotion(next_emotion, "transition")
                    
                    if bridge_music and os.path.exists(bridge_music):
                        bridge = AudioSegment.from_file(bridge_music)
                        
                        # Kort bridge: 2-3 sekunder
                        bridge = bridge[10000:13000]  # Ta mitten av spåret
                        bridge = bridge.fade_in(800).fade_out(800)  # Mjuka övergångar
                        bridge = bridge - 20  # Lägre volym än tal
                        
                        combined += bridge
                        logger.info(f"🎵 Added {next_emotion} bridge after segment {i+1}")
                
                # För sista segmentet: kort outro-musik
                if i == len(segments) - 1:
                    outro_music = self.get_music_for_emotion("professional", "outro")
                    if outro_music and os.path.exists(outro_music):
                        outro = AudioSegment.from_file(outro_music)[-5000:]  # Sista 5 sekunder
                        outro = outro.fade_in(1000) - 18  # Fade in, lägre volym
                        combined += outro
            
            # Normalisera och exportera
            combined = normalize(combined)
            combined.export(output_file, format="mp3")
            
            logger.info(f"✅ Podcast with musical bridges created: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating podcast with bridges: {e}")
            return False

    def create_segment_with_music(self, speech_file: str, emotion: str, 
                                output_file: str, category: str = "news") -> bool:
        """
        DEPRECATED: Använd create_podcast_with_musical_bridges istället
        Skapa ett segment med tal + passande bakgrundsmusik
        """
        logger.warning("create_segment_with_music is deprecated, copying speech only")
        try:
            speech = AudioSegment.from_file(speech_file)
            speech.export(output_file, format="mp3")
            return True
        except Exception as e:
            logger.error(f"Error copying speech file: {e}")
            return False
    
    def combine_segments_with_transitions(self, segments: List[Dict], output_file: str) -> bool:
        """
        Kombinera flera segment med transitions-musik
        
        Args:
            segments: Lista med {'file': path, 'emotion': str}
            output_file: Final utdata-fil
        
        Returns:
            True om framgångsrik
        """
        try:
            combined = AudioSegment.empty()
            
            for i, segment in enumerate(segments):
                # Ladda segment
                segment_audio = AudioSegment.from_file(segment['file'])
                combined += segment_audio
                
                # Lägg till transition mellan segment (förutom sista)
                if i < len(segments) - 1:
                    transition_music = self.get_music_for_emotion("professional", "transition")
                    if transition_music and os.path.exists(transition_music):
                        transition = AudioSegment.from_file(transition_music)
                        # Kort transition (2-3 sekunder)
                        transition = transition[:3000].fade_in(500).fade_out(500)
                        transition = transition - 25  # Lägre volym
                        combined += transition
            
            # Exportera final fil
            combined = normalize(combined)
            combined.export(output_file, format="mp3")
            
            logger.info(f"✅ Combined segments with transitions: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error combining segments: {e}")
            return False

def test_music_mixer():
    """Test music mixer functionality"""
    mixer = MusicMixer()
    
    print("🎵 Testing Music Mixer")
    print("=" * 40)
    
    # Test emotion mapping
    emotions = ['exciting', 'serious', 'friendly', 'professional']
    
    for emotion in emotions:
        music_file = mixer.get_music_for_emotion(emotion)
        if music_file:
            print(f"✅ {emotion}: {os.path.basename(music_file)}")
        else:
            print(f"❌ {emotion}: No music found")

if __name__ == "__main__":
    test_music_mixer()
