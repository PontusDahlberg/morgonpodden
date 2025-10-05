#!/usr/bin/env python3
"""
Episode History Manager för MMM Senaste Nytt
Hanterar historik av tidigare podcast-avsnitt för RSS-feed
"""

import json
import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class EpisodeHistory:
    """Klass för att hantera episodhistorik"""
    
    def __init__(self, history_file: str = "episode_history.json"):
        self.history_file = history_file
        self.max_episodes = 50  # Behåll max 50 avsnitt i RSS-feed
        
    def load_history(self) -> List[Dict]:
        """Ladda befintlig episodhistorik"""
        if not os.path.exists(self.history_file):
            logger.info("[HISTORY] Ingen episodhistorik hittades, skapar ny")
            return []
            
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"[HISTORY] Laddade {len(data)} episoder från historik")
                return data
        except Exception as e:
            logger.error(f"[HISTORY] Fel vid laddning av historik: {e}")
            return []
    
    def save_history(self, episodes: List[Dict]) -> bool:
        """Spara episodhistorik"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(episodes, f, indent=2, ensure_ascii=False)
            logger.info(f"[HISTORY] Sparade {len(episodes)} episoder till historik")
            return True
        except Exception as e:
            logger.error(f"[HISTORY] Fel vid sparande av historik: {e}")
            return False
    
    def add_episode(self, episode_data: Dict) -> List[Dict]:
        """Lägg till ny episod till historik och returnera uppdaterad lista"""
        # Ladda befintlig historik
        episodes = self.load_history()
        
        # Kontrollera om episoden redan finns (baserat på GUID)
        episode_guid = episode_data.get('guid', '')
        existing_episode = None
        
        for i, existing in enumerate(episodes):
            if existing.get('guid') == episode_guid:
                existing_episode = i
                break
        
        if existing_episode is not None:
            # Uppdatera befintlig episod
            episodes[existing_episode] = episode_data
            logger.info(f"[HISTORY] Uppdaterade befintlig episod: {episode_data.get('title', 'Okänd titel')}")
        else:
            # Lägg till ny episod först i listan (senaste först)
            episodes.insert(0, episode_data)
            logger.info(f"[HISTORY] Lade till ny episod: {episode_data.get('title', 'Okänd titel')}")
        
        # Begränsa antal episoder
        if len(episodes) > self.max_episodes:
            removed_count = len(episodes) - self.max_episodes
            episodes = episodes[:self.max_episodes]
            logger.info(f"[HISTORY] Tog bort {removed_count} gamla episoder (behåller {self.max_episodes})")
        
        # Spara uppdaterad historik
        self.save_history(episodes)
        
        return episodes
    
    def get_recent_episodes(self, count: int = 10) -> List[Dict]:
        """Hämta de senaste episoderna"""
        episodes = self.load_history()
        return episodes[:count]
    
    def cleanup_old_episodes(self, days: int = 30) -> int:
        """Ta bort episoder äldre än angivet antal dagar"""
        episodes = self.load_history()
        cutoff_date = datetime.now(timezone.utc).timestamp() - (days * 24 * 60 * 60)
        
        filtered_episodes = []
        removed_count = 0
        
        for episode in episodes:
            # Försök parsa pub_date
            try:
                pub_date_str = episode.get('pub_date', '')
                if pub_date_str:
                    # Konvertera från RSS-format till timestamp
                    pub_date = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %z')
                    if pub_date.timestamp() >= cutoff_date:
                        filtered_episodes.append(episode)
                    else:
                        removed_count += 1
                else:
                    # Behåll episoder utan datum
                    filtered_episodes.append(episode)
            except Exception:
                # Behåll episoder där vi inte kan parsa datumet
                filtered_episodes.append(episode)
        
        if removed_count > 0:
            self.save_history(filtered_episodes)
            logger.info(f"[HISTORY] Tog bort {removed_count} episoder äldre än {days} dagar")
        
        return removed_count

def migrate_existing_episode() -> Dict:
    """Migrera befintlig episod från public/feed.xml"""
    try:
        import xml.etree.ElementTree as ET
        
        feed_path = "public/feed.xml"
        if not os.path.exists(feed_path):
            return {}
        
        tree = ET.parse(feed_path)
        root = tree.getroot()
        
        # Hitta första item
        item = root.find('.//item')
        if item is None:
            return {}
        
        episode_data = {}
        
        # Extrahera data från XML
        title_elem = item.find('title')
        if title_elem is not None:
            episode_data['title'] = title_elem.text
        
        desc_elem = item.find('description') 
        if desc_elem is not None:
            episode_data['description'] = desc_elem.text
        
        pubdate_elem = item.find('pubDate')
        if pubdate_elem is not None:
            episode_data['pub_date'] = pubdate_elem.text
        
        guid_elem = item.find('guid')
        if guid_elem is not None:
            episode_data['guid'] = guid_elem.text
        
        enclosure_elem = item.find('enclosure')
        if enclosure_elem is not None:
            episode_data['audio_url'] = enclosure_elem.get('url', '')
            episode_data['file_size'] = int(enclosure_elem.get('length', '0'))
        
        if episode_data.get('title'):
            logger.info(f"[MIGRATION] Migrerade episod: {episode_data['title']}")
            return episode_data
        
    except Exception as e:
        logger.error(f"[MIGRATION] Fel vid migrering: {e}")
    
    return {}

# Test-funktion
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    history = EpisodeHistory()
    
    # Testa migrering
    existing = migrate_existing_episode()
    if existing:
        episodes = history.add_episode(existing)
        print(f"Migrerade och sparade {len(episodes)} episoder")
    else:
        print("Ingen befintlig episod att migrera")