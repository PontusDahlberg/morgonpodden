#!/usr/bin/env python3
"""
Music Metadata Manager för MMM Senaste Nytt
Hantera metadata för musikbibliotek med taggar, mood, tempo etc.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import hashlib

logger = logging.getLogger(__name__)

class MusicMetadataManager:
    """Hantera metadata för musikbibliotek"""
    
    def __init__(self, music_dir: str = "audio/music", metadata_file: str = "music_metadata.json"):
        self.music_dir = music_dir
        self.metadata_file = metadata_file
        self.metadata = self.load_metadata()
        
    def load_metadata(self) -> Dict:
        """Ladda befintlig metadata"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Fel vid laddning av metadata: {e}")
        
        return {
            "tracks": {},
            "last_updated": None,
            "version": "2.0"
        }
    
    def save_metadata(self) -> bool:
        """Spara metadata till fil"""
        try:
            self.metadata["last_updated"] = datetime.now().isoformat()
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"Metadata sparad: {self.metadata_file}")
            return True
        except Exception as e:
            logger.error(f"Fel vid sparande av metadata: {e}")
            return False
    
    def get_file_hash(self, filepath: str) -> str:
        """Skapa hash för fil för att identifiera ändringar"""
        try:
            with open(filepath, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()[:8]
            return file_hash
        except Exception:
            return datetime.now().strftime("%Y%m%d")
    
    def scan_music_files(self) -> List[str]:
        """Skanna musik-mappen efter MP3-filer"""
        music_files = []
        if os.path.exists(self.music_dir):
            for filename in os.listdir(self.music_dir):
                if filename.lower().endswith('.mp3'):
                    full_path = os.path.join(self.music_dir, filename)
                    music_files.append(full_path)
        return music_files
    
    def auto_detect_metadata(self, filename: str) -> Dict:
        """Försök auto-detektera metadata från filnamn"""
        basename = os.path.splitext(os.path.basename(filename))[0].lower()
        
        metadata = {
            "moods": [],
            "tempo": "medium",
            "energy": "medium",
            "categories": ["background"],
            "intensity": "medium"
        }
        
        # Auto-detektering baserat på filnamn
        mood_keywords = {
            "calm": ["calm", "lugn", "stilla", "mjuk"],
            "energetic": ["energetic", "energisk", "upp", "livlig"],
            "mysterious": ["mystery", "mystisk", "dark", "mörk"],
            "uplifting": ["uplifting", "positiv", "glad", "happy"],
            "dramatic": ["dramatic", "dramatisk", "intense", "kraftfull"],
            "peaceful": ["peace", "fredlig", "ro", "harmoni"],
            "playful": ["playful", "lekfull", "rolig", "munter"]
        }
        
        tempo_keywords = {
            "slow": ["slow", "långsam", "lugn"],
            "medium": ["medium", "medel"],
            "fast": ["fast", "snabb", "tempo", "beat"]
        }
        
        energy_keywords = {
            "low": ["low", "låg", "mjuk", "stilla"],
            "medium": ["medium", "medel"],
            "high": ["high", "hög", "energi", "kraft"]
        }
        
        # Analysera filnamn
        for mood, keywords in mood_keywords.items():
            if any(keyword in basename for keyword in keywords):
                metadata["moods"].append(mood)
        
        for tempo, keywords in tempo_keywords.items():
            if any(keyword in basename for keyword in keywords):
                metadata["tempo"] = tempo
                break
        
        for energy, keywords in energy_keywords.items():
            if any(keyword in basename for keyword in keywords):
                metadata["energy"] = energy
                break
        
        # Default mood om inget hittas
        if not metadata["moods"]:
            metadata["moods"] = ["neutral"]
            
        return metadata
    
    def update_track_metadata(self, filepath: str, custom_metadata: Dict = None) -> str:
        """Uppdatera metadata för en specifik låt"""
        filename = os.path.basename(filepath)
        file_id = self.get_file_hash(filepath)
        
        # Börja med auto-detekterade data
        track_data = {
            "id": file_id,
            "filename": filename,
            "path": filepath.replace("\\", "/"),  # Normalisera sökvägar
            "title": os.path.splitext(filename)[0],
            "file_size": os.path.getsize(filepath) if os.path.exists(filepath) else 0,
            "added_at": datetime.now().isoformat(),
            **self.auto_detect_metadata(filepath)
        }
        
        # Lägg till custom metadata om det finns
        if custom_metadata:
            track_data.update(custom_metadata)
        
        # Spara i bibliotek
        self.metadata["tracks"][file_id] = track_data
        
        logger.info(f"Uppdaterade metadata för: {filename}")
        return file_id
    
    def sync_with_filesystem(self) -> Dict:
        """Synkronisera metadata med aktuella filer"""
        current_files = self.scan_music_files()
        existing_tracks = set(self.metadata["tracks"].keys())
        
        stats = {
            "found": len(current_files),
            "added": 0,
            "updated": 0,
            "removed": 0
        }
        
        # Lägg till nya filer
        for filepath in current_files:
            file_id = self.get_file_hash(filepath)
            if file_id not in self.metadata["tracks"]:
                self.update_track_metadata(filepath)
                stats["added"] += 1
            else:
                # Uppdatera befintlig om filen har ändrats
                current_size = os.path.getsize(filepath)
                stored_size = self.metadata["tracks"][file_id].get("file_size", 0)
                if current_size != stored_size:
                    self.update_track_metadata(filepath)
                    stats["updated"] += 1
        
        # Ta bort metadata för filer som inte längre finns
        current_file_ids = set(self.get_file_hash(f) for f in current_files)
        for track_id in list(self.metadata["tracks"].keys()):
            if track_id not in current_file_ids:
                del self.metadata["tracks"][track_id]
                stats["removed"] += 1
        
        self.save_metadata()
        logger.info(f"Synkronisering klar: {stats}")
        return stats
    
    def search_tracks(self, mood: str = None, tempo: str = None, energy: str = None, 
                     intensity: str = None, category: str = None) -> List[Dict]:
        """Sök låtar baserat på metadata"""
        results = []
        
        for track_id, track in self.metadata["tracks"].items():
            match = True
            
            if mood and mood not in track.get("moods", []):
                match = False
            if tempo and track.get("tempo") != tempo:
                match = False
            if energy and track.get("energy") != energy:
                match = False
            if intensity and track.get("intensity") != intensity:
                match = False
            if category and category not in track.get("categories", []):
                match = False
            
            if match:
                results.append(track)
        
        return results
    
    def get_track_info(self, filepath: str) -> Optional[Dict]:
        """Hämta metadata för specifik fil"""
        file_id = self.get_file_hash(filepath)
        return self.metadata["tracks"].get(file_id)
    
    def list_all_values(self) -> Dict[str, set]:
        """Lista alla unika värden för varje metadatatyp"""
        all_moods = set()
        all_tempos = set()
        all_energies = set()
        all_intensities = set()
        all_categories = set()
        
        for track in self.metadata["tracks"].values():
            all_moods.update(track.get("moods", []))
            all_tempos.add(track.get("tempo", ""))
            all_energies.add(track.get("energy", ""))
            all_intensities.add(track.get("intensity", ""))
            all_categories.update(track.get("categories", []))
        
        return {
            "moods": all_moods,
            "tempos": all_tempos,
            "energies": all_energies,
            "intensities": all_intensities,
            "categories": all_categories
        }

def create_sample_metadata_config():
    """Skapa exempel på hur man kan tagga låtar"""
    sample_config = {
        "MMM Senaste Nytt Från Människa Maskin Mi.mp3": {
            "moods": ["uplifting", "energetic"],
            "tempo": "medium",
            "energy": "high",
            "intensity": "medium",
            "categories": ["intro", "outro", "news"],
            "description": "Signaturmelodi för MMM Senaste Nytt - energisk och professionell"
        },
        "Vågornas Sång.mp3": {
            "moods": ["peaceful", "calm"],
            "tempo": "slow",
            "energy": "low",
            "intensity": "low",
            "categories": ["background", "transition"],
            "description": "Lugn och avslappnande bakgrundsmusik"
        },
        "Vågornas Sång (1).mp3": {
            "moods": ["peaceful", "mysterious"],
            "tempo": "slow",
            "energy": "low", 
            "intensity": "medium",
            "categories": ["background", "ambient"],
            "description": "Variant 1 - mer mystisk känsla"
        }
    }
    
    with open("sample_music_config.json", "w", encoding="utf-8") as f:
        json.dump(sample_config, f, indent=2, ensure_ascii=False)
    
    print("✅ Skapade sample_music_config.json med exempel på metadata")

# Test och exempel
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Skapa manager
    manager = MusicMetadataManager()
    
    # Synkronisera med filesystem
    print("🔄 Synkroniserar musikbibliotek...")
    stats = manager.sync_with_filesystem()
    print(f"📊 Resultat: {stats}")
    
    # Visa alla tillgängliga låtar
    print(f"\n🎵 Alla låtar ({len(manager.metadata['tracks'])}):")
    for track in manager.metadata["tracks"].values():
        print(f"- {track['filename']}: {', '.join(track.get('moods', []))}")
    
    # Visa alla metadata-värden
    print(f"\n📋 Tillgängliga metadata-värden:")
    values = manager.list_all_values()
    for key, vals in values.items():
        print(f"- {key}: {', '.join(sorted(vals))}")
    
    # Skapa exempel-config
    create_sample_metadata_config()
    print(f"\n💡 Tips: Redigera sample_music_config.json för att anpassa metadata för dina låtar!")