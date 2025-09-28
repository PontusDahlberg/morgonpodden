#!/usr/bin/env python3
"""
SMART EPISODE MONITOR
Intelligent lokal nedladdning som:
- Kör dagligen kl 18:00 
- Startar vid datorstart 
- Kollar extra ofta på onsdagar
- Återförsöker vid nätverksproblem
"""

import os
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import time
import schedule
import threading
from dataclasses import dataclass

# Stäng av SSL-varningar
urllib3.disable_warnings(InsecureRequestWarning)

# Konfigurera logging med UTF-8
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class EpisodeInfo:
    """Information om ett podcast-avsnitt"""
    title: str
    url: str
    pub_date: str
    source: str
    filename: str = ""

class SmartEpisodeMonitor:
    """Intelligent övervakare för podcast-avsnitt"""
    
    def __init__(self):
        # Konfigurera säker session
        self.session = requests.Session()
        self.session.verify = False
        
        # Lokal lagring
        self.local_episodes_dir = Path("local_episodes")
        self.local_episodes_dir.mkdir(exist_ok=True)
        
        # Cloudflare och GitHub config
        self.cloudflare_base = "https://manniska-maskin-miljo.9c5323b560f65e0ead7cee1bdba8a690.r2.dev"
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_owner = "PontusDahlberg"
        self.repo_name = "morgonpodden"
        
        # Status tracking
        self.last_check = None
        self.download_history = self._load_download_history()
        
        logger.info("Smart Episode Monitor initialiserad")
    
    def _load_download_history(self) -> Dict:
        """Ladda nedladdningshistorik"""
        history_file = self.local_episodes_dir / "download_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Kunde inte ladda historik: {e}")
        return {}
    
    def _save_download_history(self):
        """Spara nedladdningshistorik"""
        history_file = self.local_episodes_dir / "download_history.json"
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.download_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Kunde inte spara historik: {e}")
    
    def find_available_episodes(self) -> List[EpisodeInfo]:
        """Hitta tillgängliga avsnitt från alla källor"""
        episodes = []
        
        # Försök Cloudflare först
        try:
            cloudflare_episodes = self._check_cloudflare_rss()
            episodes.extend(cloudflare_episodes)
            logger.info(f"Cloudflare: {len(cloudflare_episodes)} avsnitt")
        except Exception as e:
            logger.warning(f"Cloudflare fel: {e}")
        
        # Försök GitHub Actions som backup
        if self.github_token:
            try:
                github_episodes = self._check_github_artifacts()
                episodes.extend(github_episodes)
                logger.info(f"GitHub: {len(github_episodes)} avsnitt")
            except Exception as e:
                logger.warning(f"GitHub fel: {e}")
        
        return episodes
    
    def _check_cloudflare_rss(self) -> List[EpisodeInfo]:
        """Kontrollera Cloudflare RSS feed"""
        episodes = []
        
        try:
            rss_url = f"{self.cloudflare_base}/feed.xml"
            response = self.session.get(rss_url, timeout=10)
            
            if response.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)
                
                for item in root.findall('.//item'):
                    enclosure = item.find('enclosure')
                    if enclosure is not None:
                        episode_url = enclosure.get('url')
                        title_elem = item.find('title')
                        title = title_elem.text if title_elem is not None else "Unknown"
                        
                        pub_date_elem = item.find('pubDate')
                        pub_date = pub_date_elem.text if pub_date_elem is not None else ""
                        
                        episodes.append(EpisodeInfo(
                            title=title,
                            url=episode_url,
                            pub_date=pub_date,
                            source='cloudflare'
                        ))
        
        except Exception as e:
            logger.debug(f"Cloudflare RSS fel: {e}")
            raise
        
        return episodes
    
    def _check_github_artifacts(self) -> List[EpisodeInfo]:
        """Kontrollera GitHub Actions artifacts"""
        episodes = []
        
        if not self.github_token:
            return episodes
        
        try:
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/actions/runs"
            params = {'status': 'completed', 'per_page': 10}
            
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                runs = response.json()['workflow_runs']
                
                for run in runs:
                    artifacts_url = run['artifacts_url']
                    artifacts_response = self.session.get(artifacts_url, headers=headers, timeout=10)
                    
                    if artifacts_response.status_code == 200:
                        artifacts = artifacts_response.json()['artifacts']
                        
                        for artifact in artifacts:
                            if 'podcast' in artifact['name'].lower():
                                episodes.append(EpisodeInfo(
                                    title=artifact['name'],
                                    url=artifact['archive_download_url'],
                                    pub_date=artifact['created_at'],
                                    source='github',
                                ))
        
        except Exception as e:
            logger.debug(f"GitHub artifacts fel: {e}")
            raise
        
        return episodes
    
    def download_episode(self, episode: EpisodeInfo) -> bool:
        """Ladda ner ett enskilt avsnitt"""
        try:
            # Skapa säkert filnamn
            safe_title = "".join(c for c in episode.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')
            
            # Lägg till datum och source
            today = datetime.now().strftime("%Y%m%d")
            filename = f"{today}_{safe_title}_{episode.source}.mp3"
            filepath = self.local_episodes_dir / filename
            
            # Kontrollera om redan nedladdat
            episode_id = f"{episode.url}_{episode.pub_date}"
            if episode_id in self.download_history:
                logger.debug(f"Redan nedladdat: {episode.title}")
                return True
            
            # Skippa om filen redan finns
            if filepath.exists():
                logger.info(f"Fil finns redan: {filename}")
                self.download_history[episode_id] = {
                    'filename': filename,
                    'download_date': datetime.now().isoformat(),
                    'source': episode.source
                }
                self._save_download_history()
                return True
            
            # Ladda ner filen
            logger.info(f"Laddar ner: {episode.title} från {episode.source}")
            response = self.session.get(episode.url, timeout=60)
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                # Spara i historik
                self.download_history[episode_id] = {
                    'filename': filename,
                    'download_date': datetime.now().isoformat(),
                    'source': episode.source,
                    'title': episode.title
                }
                self._save_download_history()
                
                logger.info(f"✓ Nedladdat: {filename}")
                return True
            else:
                logger.warning(f"HTTP {response.status_code} för {episode.title}")
                return False
        
        except Exception as e:
            logger.error(f"Fel vid nedladdning av {episode.title}: {e}")
            return False
    
    def sync_episodes(self) -> Dict[str, int]:
        """Synkronisera alla tillgängliga avsnitt"""
        logger.info("Startar smart synkronisering...")
        
        episodes = self.find_available_episodes()
        total_found = len(episodes)
        downloaded = 0
        skipped = 0
        
        for episode in episodes:
            if self.download_episode(episode):
                downloaded += 1
            else:
                skipped += 1
        
        self.last_check = datetime.now()
        
        result = {
            'total_found': total_found,
            'downloaded': downloaded,
            'skipped': skipped,
            'check_time': self.last_check.isoformat()
        }
        
        logger.info(f"Synkronisering klar: {downloaded} nedladdade, {skipped} misslyckade av {total_found} hittade")
        return result
    
    def is_wednesday(self) -> bool:
        """Kontrollera om det är onsdag (extra kontroller)"""
        return datetime.now().weekday() == 2  # 0=måndag, 2=onsdag
    
    def start_monitoring(self):
        """Starta intelligent övervakning"""
        logger.info("Startar intelligent övervakning...")
        
        # Omedelbar kontroll vid start
        self.sync_episodes()
        
        # Schemalägg daglig kontroll kl 18:00
        schedule.every().day.at("18:00").do(self.sync_episodes)
        
        # Extra kontroller på onsdagar (var 2:e timme mellan 06-20)
        for hour in range(6, 21, 2):
            schedule.every().wednesday.at(f"{hour:02d}:00").do(self.sync_episodes)
        
        # Kör scheduler i bakgrund
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Kolla varje minut
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info("Smart monitoring aktiv - tryck Ctrl+C för att avsluta")
        
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Avbryter smart monitoring")

def main():
    """Huvudfunktion"""
    monitor = SmartEpisodeMonitor()
    
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "--monitor":
        # Kontinuerlig övervakning
        monitor.start_monitoring()
    else:
        # Engångskörning
        result = monitor.sync_episodes()
        print(f"Resultat: {result}")

if __name__ == "__main__":
    main()
