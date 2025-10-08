#!/usr/bin/env python3
"""
Music Metadata Configurator
Enkelt verktyg för att applicera metadata på musikfiler
"""

import json
import os
from music_metadata_manager import MusicMetadataManager

def apply_custom_metadata():
    """Applicera custom metadata från config-fil"""
    manager = MusicMetadataManager()
    
    # Ladda custom konfiguration  
    config_file = "complete_music_config.json"
    if not os.path.exists(config_file):
        print(f"❌ {config_file} hittades inte. Kör music_metadata_manager.py först.")
        return
    
    with open(config_file, 'r', encoding='utf-8') as f:
        custom_config = json.load(f)
    
    print(f"📝 Applicerar metadata från {config_file}...")
    
    applied = 0
    for filename, metadata in custom_config.items():
        filepath = os.path.join("audio/music", filename)
        if os.path.exists(filepath):
            manager.update_track_metadata(filepath, metadata)
            applied += 1
            print(f"✅ {filename}: {', '.join(metadata.get('moods', []))}")
        else:
            print(f"❌ {filename}: Fil hittades inte")
    
    manager.save_metadata()
    print(f"\n🎉 Applicerat metadata på {applied} låtar!")
    
    # Visa resultat
    print(f"\n🎵 Uppdaterat musikbibliotek:")
    for track in manager.metadata["tracks"].values():
        moods = ', '.join(track.get('moods', []))
        tempo = track.get('tempo', '')
        energy = track.get('energy', '')
        print(f"- {track['filename']}: {moods} | {tempo} tempo | {energy} energy")

def search_music_demo():
    """Demonstrera sökfunktionalitet"""
    manager = MusicMetadataManager()
    
    print(f"\n🔍 Sökexempel:")
    
    # Sök lugn musik
    calm_tracks = manager.search_tracks(mood="calm")
    print(f"\n🧘 Lugn musik ({len(calm_tracks)} träffar):")
    for track in calm_tracks:
        print(f"- {track['filename']}")
    
    # Sök energisk musik
    energetic_tracks = manager.search_tracks(mood="energetic")
    print(f"\n⚡ Energisk musik ({len(energetic_tracks)} träffar):")
    for track in energetic_tracks:
        print(f"- {track['filename']}")
    
    # Sök låg energi
    low_energy = manager.search_tracks(energy="low")
    print(f"\n🔋 Låg energi ({len(low_energy)} träffar):")
    for track in low_energy:
        print(f"- {track['filename']}")
    
    # Sök bakgrundsmusik
    background = manager.search_tracks(category="background")
    print(f"\n🎶 Bakgrundsmusik ({len(background)} träffar):")
    for track in background:
        print(f"- {track['filename']}")

if __name__ == "__main__":
    apply_custom_metadata()
    search_music_demo()