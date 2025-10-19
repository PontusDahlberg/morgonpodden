#!/usr/bin/env python3
"""
AUTOMATISK LOKAL LAGRING
Hämtar nya avsnitt från GitHub Actions automatiskt
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

# Stäng av SSL-varningar för lokal utveckling
urllib3.disable_warnings(InsecureRequestWarning)

# Konfigurera logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_download.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EpisodeDownloader:
    """Automatisk nedladdare för podcast-avsnitt"""
    
    def __init__(self):
        # Konfigurera en säker session
        self.session = requests.Session()
        self.session.verify = False  # Stäng av SSL-verifiering
        
        self.local_episodes_dir = Path("local_episodes")
        self.local_episodes_dir.mkdir(exist_ok=True)
        
        # GitHub API för artifacts (kräver token för privata repos)
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_owner = "PontusDahlberg"
        self.repo_name = "morgonpodden"
        
        logger.info("Episode Downloader initialiserad")
    
    def check_for_new_episodes(self) -> List[Dict]:
        """Kolla efter nya avsnitt från GitHub Actions"""
        logger.info("Letar efter nya avsnitt...")
        
        new_episodes = []
        
        # Kolla GitHub Actions artifacts
        if self.github_token:
            github_episodes = self._check_github_artifacts()
            new_episodes.extend(github_episodes)
        else:
            logger.info("ℹ️ Ingen GitHub token konfigurerad")
        
        return new_episodes
    

    
    def _check_github_artifacts(self) -> List[Dict]:
        """Kolla GitHub Actions artifacts för nya avsnitt"""
        episodes = []
        
        if not self.github_token:
            logger.info("ℹ️ Ingen GitHub token - skippar artifact-sökning")
            return episodes
        
        try:
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Hämta senaste workflow runs
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/actions/runs"
            params = {
                'status': 'completed',
                'per_page': 10
            }
            
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                runs = response.json()['workflow_runs']
                
                for run in runs:
                    # Kolla artifacts för denna run
                    artifacts_url = run['artifacts_url']
                    artifacts_response = self.session.get(artifacts_url, headers=headers, timeout=10)
                    
                    if artifacts_response.status_code == 200:
                        artifacts = artifacts_response.json()['artifacts']
                        
                        for artifact in artifacts:
                            if 'episode' in artifact['name'].lower():
                                episodes.append({
                                    'url': artifact['archive_download_url'],
                                    'title': artifact['name'],
                                    'created_at': artifact['created_at'],
                                    'source': 'github',
                                    'headers': headers  # Behövs för autentisering
                                })
                
                logger.info(f"✅ Hittade {len(episodes)} artifacts på GitHub")
        
        except Exception as e:
            logger.warning(f"⚠️ Kunde inte komma åt GitHub: {e}")
        
        return episodes
    
    def download_episode(self, episode: Dict) -> bool:
        """Ladda ner ett enskilt avsnitt"""
        try:
            # Skapa filnamn baserat på titel och datum
            safe_title = "".join(c for c in episode['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')
            
            # Lägg till datum för unikhet
            today = datetime.now().strftime("%Y%m%d")
            filename = f"{today}_{safe_title}.mp3"
            filepath = self.local_episodes_dir / filename
            
            # Skippa om filen redan finns
            if filepath.exists():
                logger.info(f"⏭️ Avsnitt finns redan: {filename}")
                return True
            
            # Ladda ner filen med SSL-konfiguration
            headers = episode.get('headers', {})
            response = self.session.get(episode['url'], headers=headers, timeout=30)
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                file_size = filepath.stat().st_size
                logger.info(f"✅ Nedladdat: {filename} ({file_size:,} bytes)")
                
                # Spara metadata
                self._save_episode_metadata(episode, filepath)
                return True
            else:
                logger.error(f"❌ Fel vid nedladdning: {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Fel vid nedladdning av {episode['title']}: {e}")
            return False
    
    def _save_episode_metadata(self, episode: Dict, filepath: Path):
        """Spara metadata för avsnittet"""
        metadata_file = filepath.with_suffix('.json')
        
        metadata = {
            'title': episode['title'],
            'source': episode['source'],
            'download_date': datetime.now().isoformat(),
            'original_url': episode['url'],
            'file_size': filepath.stat().st_size
        }
        
        if 'pub_date' in episode:
            metadata['pub_date'] = episode['pub_date']
        if 'created_at' in episode:
            metadata['created_at'] = episode['created_at']
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def sync_all_episodes(self):
        """Synkronisera alla nya avsnitt"""
        logger.info("🔄 Startar automatisk synkronisering...")
        
        try:
            new_episodes = self.check_for_new_episodes()
            
            if not new_episodes:
                logger.info("ℹ️ Inga nya avsnitt hittade")
                return
            
            downloaded = 0
            for episode in new_episodes:
                if self.download_episode(episode):
                    downloaded += 1
                time.sleep(1)  # Vänta mellan nedladdningar
            
            logger.info(f"✅ Synkronisering klar: {downloaded}/{len(new_episodes)} avsnitt nedladdade")
        
        except Exception as e:
            logger.error(f"❌ Fel vid synkronisering: {e}")
    
    def start_automatic_monitoring(self):
        """Starta automatisk övervakning"""
        logger.info("🤖 Startar automatisk övervakning...")
        
        # Schemalägg kontroller
        schedule.every(30).minutes.do(self.sync_all_episodes)  # Var 30:e minut
        schedule.every().day.at("07:30").do(self.sync_all_episodes)  # Daglig kontroll
        
        # Första synkroniseringen direkt
        self.sync_all_episodes()
        
        # Kör i loop
        logger.info("⏰ Automatisk övervakning aktiv (Ctrl+C för att stoppa)")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Kolla varje minut
        except KeyboardInterrupt:
            logger.info("🛑 Automatisk övervakning stoppad")

def main():
    """Huvudfunktion"""
    downloader = EpisodeDownloader()
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        # Starta automatisk övervakning
        downloader.start_automatic_monitoring()
    else:
        # Kör en gång
        downloader.sync_all_episodes()

if __name__ == "__main__":
    main()
