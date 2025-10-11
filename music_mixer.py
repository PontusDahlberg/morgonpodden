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

# Import metadata manager
try:
    from music_metadata_manager import MusicMetadataManager
    METADATA_AVAILABLE = True
except ImportError:
    METADATA_AVAILABLE = False
    logger.warning("MusicMetadataManager inte tillgänglig, använder fallback-metod")

class MusicMixer:
    def __init__(self, music_library_path: str = "music_library.json"):
        self.music_library_path = music_library_path
        self.music_library = self.load_music_library()
        
        # Initiera metadata manager om tillgänglig
        if METADATA_AVAILABLE:
            self.metadata_manager = MusicMetadataManager()
        else:
            self.metadata_manager = None
        
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
    
    def get_music_by_metadata(self, mood: str = None, tempo: str = None, energy: str = None, 
                             intensity: str = None, category: str = None, exclude: List[str] = None) -> Optional[str]:
        """
        Välj musik baserat på metadata-taggar
        
        Args:
            mood: Mood som "calm", "energetic", "peaceful", "uplifting"
            tempo: Tempo som "slow", "medium", "fast"
            energy: Energinivå som "low", "medium", "high"
            intensity: Intensitet som "low", "medium", "high"
            category: Kategori som "background", "intro", "outro"
            exclude: Lista med filer att undvika
        
        Returns:
            Sökväg till vald musikfil eller None
        """
        if not self.metadata_manager:
            logger.warning("Metadata manager inte tillgänglig, använder fallback")
            return None
        
        # Sök matchande låtar
        matching_tracks = self.metadata_manager.search_tracks(
            mood=mood, tempo=tempo, energy=energy, 
            intensity=intensity, category=category
        )
        
        # Filtrera bort excluded filer
        if exclude:
            exclude_basenames = [os.path.basename(path) for path in exclude]
            matching_tracks = [
                track for track in matching_tracks 
                if track["filename"] not in exclude_basenames
            ]
        
        if matching_tracks:
            # Välj slumpmässigt från matchande
            selected_track = random.choice(matching_tracks)
            logger.info(f"🎵 Valde från metadata: {selected_track['filename']} "
                       f"(mood: {', '.join(selected_track.get('moods', []))}, "
                       f"tempo: {selected_track.get('tempo', 'N/A')}, "
                       f"energy: {selected_track.get('energy', 'N/A')})")
            return selected_track["path"]
        
        logger.warning(f"Ingen musik matchade metadata: mood={mood}, tempo={tempo}, energy={energy}")
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
                
                # För första segmentet: alltid använd "Mellan Dröm och Verklighet" som intro
                if i == 0:
                    intro_music_path = os.path.join(os.path.dirname(__file__), "audio", "music", "Mellan Dröm och Verklighet.mp3")
                    if os.path.exists(intro_music_path):
                        intro = AudioSegment.from_file(intro_music_path)[:4000]  # 4 sekunder
                        intro = intro.fade_out(1000) - 15  # Fade ut, lägre volym
                        combined += intro
                        logger.info("🎵 Använder fast intro: Mellan Dröm och Verklighet")
                    else:
                        # Fallback till gammal metod om filen inte hittas
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
    
    def create_varied_music_background(self, speech_file: str, available_music: List[str], 
                                     output_file: str, music_volume: float = -15, 
                                     segment_duration: int = 60, fade_duration: int = 3000) -> bool:
        """
        Skapa bakgrundsmusik som varierar under avsnittet
        
        Args:
            speech_file: Sökväg till tal-audio
            available_music: Lista med tillgängliga musikfiler
            output_file: Utdata-fil
            music_volume: Musik-volym i dB (negativ för lägre)
            segment_duration: Sekunder innan musik byts (60s default)
            fade_duration: Crossfade mellan låtar i ms (3s default)
        
        Returns:
            True om framgångsrik, False annars
        """
        try:
            if not available_music:
                logger.error("Ingen musik tillgänglig för varierad bakgrund")
                return False
            
            # Ladda tal-audio
            speech = AudioSegment.from_file(speech_file)
            speech_duration_ms = len(speech)
            segment_duration_ms = segment_duration * 1000
            
            logger.info(f"🎵 Skapar varierad musikbakgrund för {speech_duration_ms/1000:.1f}s tal")
            logger.info(f"🎵 Använder {len(available_music)} låtar, byter var {segment_duration}s")
            
            # Skapa tom bakgrundsmusik
            background = AudioSegment.silent(duration=speech_duration_ms)
            
            # Skapa smart musikurval baserat på metadata om möjligt
            import random
            
            # Definiera olika "zoner" för podcast med olika krav
            music_zones = [
                {"mood": "uplifting", "energy": "medium", "name": "Intro"},
                {"mood": "calm", "energy": "low", "name": "Bakgrund"},
                {"mood": "energetic", "energy": "high", "name": "Höjdpunkt"},
                {"mood": "peaceful", "energy": "low", "name": "Transition"}
            ]
            
            # Skapa musik-kö med variation
            music_queue = []
            used_tracks = []
            
            # ALLTID använd "Mellan Dröm och Verklighet" som FÖRSTA intro (samma som MMM huvudpodden)
            # Men ALDRIG i bakgrundsmusik eller senare segment
            intro_track = None
            intro_only_music = []
            for track in available_music:
                if "Mellan Dröm och Verklighet" in track:
                    intro_track = track
                    intro_only_music.append(track)  # Spara intro-musik separat
                    break
            
            if intro_track:
                music_queue.append(intro_track)
                used_tracks.append(intro_track)
                logger.info("🎵 Fast intro: Mellan Dröm och Verklighet (samma som MMM huvudpodden)")
            
            # Filtrera bort intro-musik från tillgänglig musik för bakgrund
            background_music = [m for m in available_music if m not in intro_only_music]
            
            # Försök använda metadata-baserat urval för övriga zoner
            if self.metadata_manager:
                for zone in music_zones[1:]:  # Hoppa över intro, redan fixerad
                    track_path = self.get_music_by_metadata(
                        mood=zone["mood"], 
                        energy=zone["energy"],
                        exclude=used_tracks
                    )
                    if track_path:
                        music_queue.append(track_path)
                        used_tracks.append(track_path)
                        logger.info(f"🎵 Zon '{zone['name']}': {os.path.basename(track_path)}")
            
            # Fyll upp med resterande musik slumpmässigt (UTAN intro-musik)
            remaining_music = [m for m in background_music if m not in music_queue]
            random.shuffle(remaining_music)
            music_queue.extend(remaining_music)
            
            # Fallback om metadata inte fungerade (använd background_music, inte available_music)
            if len(music_queue) <= 1:  # Bara intro-låt
                fallback_music = background_music.copy()
                random.shuffle(fallback_music)
                music_queue.extend(fallback_music)
            
            current_pos = 0
            music_index = 0
            
            while current_pos < speech_duration_ms:
                # Välj nästa låt (rotera genom kön)
                current_music_file = music_queue[music_index % len(music_queue)]
                music_index += 1
                
                # Ladda musikfil
                try:
                    music_segment = AudioSegment.from_file(current_music_file)
                    music_name = os.path.basename(current_music_file)
                    
                    # Justera volym
                    music_segment = music_segment + music_volume
                    
                    # Beräkna hur lång denna sektion ska vara
                    remaining_time = speech_duration_ms - current_pos
                    section_duration = min(segment_duration_ms, remaining_time)
                    
                    # Loopa musik om den är kortare än sektionen
                    while len(music_segment) < section_duration:
                        music_segment = music_segment + music_segment
                    
                    # Beskär till rätt längd
                    music_segment = music_segment[:section_duration]
                    
                    # Lägg till crossfade om det inte är första segmentet
                    if current_pos > 0 and section_duration > fade_duration * 2:
                        music_segment = music_segment.fade_in(fade_duration)
                    
                    # Lägg till fade-out om det inte är sista segmentet
                    if current_pos + section_duration < speech_duration_ms and section_duration > fade_duration * 2:
                        music_segment = music_segment.fade_out(fade_duration)
                    
                    # Lägg till musiksegment till bakgrund
                    background = background.overlay(music_segment, position=current_pos)
                    
                    logger.info(f"🎵 Segment {current_pos/1000:.1f}s-{(current_pos + section_duration)/1000:.1f}s: {music_name}")
                    
                    current_pos += section_duration
                    
                except Exception as e:
                    logger.error(f"Fel vid laddning av {current_music_file}: {e}")
                    current_pos += segment_duration_ms  # Hoppa över denna sektion
                    continue
            
            # Lägg till 10 sekunder musikuttoning efter tal  
            outro_duration_ms = 10000  # 10 sekunder
            final_audio_duration = speech_duration_ms + outro_duration_ms
            
            # Skapa längre bakgrund för att inkludera uttoning
            if current_pos < final_audio_duration:
                # Lägg till sista musiksegmentet för uttoning
                remaining_music = available_music[music_index % len(available_music)]
                try:
                    outro_music = AudioSegment.from_mp3(remaining_music)
                    outro_music = outro_music + music_volume
                    outro_section = outro_music[:outro_duration_ms]
                    # Fade ut uttoning
                    outro_section = outro_section.fade_out(3000)  # 3 sekunder fade ut
                    background = background.overlay(outro_section, position=speech_duration_ms)
                    logger.info(f"🎵 Musikuttoning: {outro_duration_ms/1000:.1f}s efter tal")
                except Exception as e:
                    logger.error(f"Fel vid uttoning: {e}")
            
            # Mixa tal med varierad bakgrundsmusik (inkl. uttoning)
            mixed = speech.overlay(background)
            
            # Normalisera och exportera
            mixed = normalize(mixed)
            mixed.export(output_file, format="mp3")
            
            logger.info(f"✅ Varierad musikmix sparad: {output_file}")
            logger.info(f"🎵 Använde {music_index} musiksegment från {len(set(available_music))} unika låtar")
            return True
            
        except Exception as e:
            logger.error(f"Fel vid skapande av varierad musikbakgrund: {e}")
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
