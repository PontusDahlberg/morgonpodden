#!/usr/bin/env python3
"""
Cloudflare R2 Uploader för Människa Maskin Miljö podcast
Använder Bearer token authentication istället för S3 credentials
"""

import requests
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Konfigurera logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloudflareUploader:
    def __init__(self):
        load_dotenv()
        
        self.account_id = "9c5323b560f65e0ead7cee1bdba8a690"
        self.api_token = os.getenv('CLOUDFLARE_API_TOKEN')
        self.bucket_name = os.getenv('CLOUDFLARE_R2_BUCKET', 'manniska-maskin-miljo')
        self.public_url = os.getenv('CLOUDFLARE_R2_PUBLIC_URL')
        
        if not self.api_token:
            raise ValueError("CLOUDFLARE_API_TOKEN not found in .env file")
        
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        logger.info(f"R2 Uploader initialiserad")
        logger.info(f"   Bucket: {self.bucket_name}")
        if self.public_url:
            logger.info(f"   Public URL: {self.public_url}")

    def upload_file(self, local_path: str, remote_path: str = None, content_type: str = None) -> str:
        """
        Upload a file to Cloudflare R2
        
        Args:
            local_path (str): Sökväg till filen som ska laddas upp
            remote_path (str, optional): Namnet på objektet i bucket
            content_type (str, optional): MIME-typ för filen
        
        Returns:
            str: Public URL till filen om lyckad, None om fel
        """
        try:
            if not os.path.exists(local_path):
                raise FileNotFoundError(f"File not found: {local_path}")
            
            if remote_path is None:
                remote_path = os.path.basename(local_path)
            
            # Bestäm content type automatiskt
            if not content_type:
                if local_path.endswith('.mp3'):
                    content_type = 'audio/mpeg'
                elif local_path.endswith('.xml'):
                    content_type = 'application/xml'
                elif local_path.endswith('.json'):
                    content_type = 'application/json'
                elif local_path.endswith('.html'):
                    content_type = 'text/html'
                elif local_path.endswith('.jpg') or local_path.endswith('.jpeg'):
                    content_type = 'image/jpeg'
                elif local_path.endswith('.png'):
                    content_type = 'image/png'
                else:
                    content_type = 'application/octet-stream'
            
            # Läs fil
            with open(local_path, 'rb') as f:
                file_data = f.read()
            
            # Cloudflare R2 API endpoint för file upload
            url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/r2/buckets/{self.bucket_name}/objects/{remote_path}"
            
            # Upload headers för binär data
            upload_headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': content_type
            }
            
            logger.info(f"Laddar upp {local_path} som {remote_path}...")
            logger.info(f"   Content-Type: {content_type}")
            
            response = requests.put(url, data=file_data, headers=upload_headers)
            
            if response.status_code in [200, 201, 204]:
                public_file_url = f"{self.public_url}/{remote_path}" if self.public_url else None
                logger.info(f"Upload lyckades: {remote_path}")
                if public_file_url:
                    logger.info(f"   Public URL: {public_file_url}")
                
                return public_file_url
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"Upload failed for {remote_path}: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"Upload failed for {local_path}: {e}")
            return None

    def upload_text(self, text_content: str, remote_path: str, content_type: str = 'text/plain') -> str:
        """
        Ladda upp text-innehåll direkt till R2
        
        Args:
            text_content (str): Text att ladda upp
            remote_path (str): Namnet på objektet i bucket
            content_type (str): MIME-typ för innehållet
        
        Returns:
            str: Public URL till filen om lyckad, None om fel
        """
        try:
            # Cloudflare R2 API endpoint för file upload
            url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/r2/buckets/{self.bucket_name}/objects/{remote_path}"
            
            # Upload headers för text data
            upload_headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': content_type
            }
            
            logger.info(f"Laddar upp text som {remote_path}...")
            
            # Konvertera text till bytes
            data = text_content.encode('utf-8') if isinstance(text_content, str) else text_content
            
            response = requests.put(url, data=data, headers=upload_headers)
            
            if response.status_code in [200, 201, 204]:
                public_file_url = f"{self.public_url}/{remote_path}" if self.public_url else None
                logger.info(f"Text upload lyckades: {remote_path}")
                if public_file_url:
                    logger.info(f"   Public URL: {public_file_url}")
                
                return public_file_url
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"Text upload failed for {remote_path}: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"Text upload failed for {remote_path}: {e}")
            return None

    def upload_episode(self, audio_file: str, metadata: Dict) -> Dict:
        """Upload an episode and its metadata"""
        episode_number = metadata['episode_number']
        
        # Upload audio file
        audio_remote = f"episodes/episode_{episode_number}.mp3"
        audio_url = self.upload_file(audio_file, audio_remote)
        
        if not audio_url:
            raise Exception(f"Failed to upload audio file: {audio_file}")
        
        # Update metadata with public URL
        metadata['audio_url'] = audio_url
        metadata['uploaded_at'] = datetime.now().isoformat()
        
        # Save and upload metadata
        meta_file = f"episodes/episode_{episode_number}_meta.json"
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        meta_remote = f"episodes/episode_{episode_number}_meta.json"
        meta_url = self.upload_file(meta_file, meta_remote)
        
        if meta_url:
            metadata['metadata_url'] = meta_url
        
        return metadata
    
    def upload_feed(self, feed_file: str = 'public/feed.xml'):
        """Upload RSS feed"""
        feed_url = self.upload_file(feed_file, 'feed.xml')
        
        # Also upload the JSON version if it exists
        json_file = feed_file.replace('.xml', '.json')
        if os.path.exists(json_file):
            json_url = self.upload_file(json_file, 'feed.json')
            logger.info(f"Uploaded JSON feed: {json_url}")
        
        return feed_url
    
    def upload_static_files(self):
        """Upload static files like images and HTML"""
        uploaded_files = []
        
        # Load config to get cover image path
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'sources.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                cover_image_path = config.get('podcastSettings', {}).get('cover_image', 'public/cover.jpg')
        except:
            cover_image_path = 'public/cover.jpg'
        
        static_files = [
            ('public/index.html', 'index.html'),
            (cover_image_path, os.path.basename(cover_image_path))
        ]
        
        # Add legacy logo.png if it exists
        if os.path.exists('public/logo.png'):
            static_files.append(('public/logo.png', 'logo.png'))
        
        for local, remote in static_files:
            if os.path.exists(local):
                url = self.upload_file(local, remote)
                if url:
                    uploaded_files.append(url)
                    logger.info(f"Uploaded static file: {local} -> {url}")
            else:
                logger.warning(f"Static file not found: {local}")
        
        return uploaded_files
    
    def sync_all_episodes(self):
        """Sync all local episodes to Cloudflare R2"""
        episodes_dir = 'episodes'
        if not os.path.exists(episodes_dir):
            logger.warning("No episodes directory found")
            return []
        
        uploaded_episodes = []
        
        for filename in os.listdir(episodes_dir):
            if filename.endswith('.mp3'):
                local_path = os.path.join(episodes_dir, filename)
                remote_path = f"episodes/{filename}"
                
                url = self.upload_file(local_path, remote_path)
                if url:
                    uploaded_episodes.append(url)
                    logger.info(f"Synced episode: {filename}")
        
        return uploaded_episodes

    def list_objects(self, max_keys: int = 1000) -> List[Dict]:
        """
        Lista objekt i bucket
        
        Args:
            max_keys (int): Max antal objekt att returnera
        
        Returns:
            list: Lista med objekt-information
        """
        try:
            url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/r2/buckets/{self.bucket_name}/objects"
            params = {'max-keys': max_keys}
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                objects = data.get('result', {}).get('objects', [])
                logger.info(f"Hittade {len(objects)} objekt i bucket")
                return objects
            else:
                logger.error(f"List failed: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"List failed: {e}")
            return []

    def test_connection(self) -> bool:
        """
        Testa anslutning genom att lista buckets
        
        Returns:
            bool: True om anslutning fungerar
        """
        try:
            url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/r2/buckets"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                buckets = data.get('result', {}).get('buckets', [])
                logger.info(f"Anslutning OK. Hittade {len(buckets)} buckets")
                
                # Kontrollera att vår bucket finns
                bucket_names = [b.get('name') for b in buckets]
                if self.bucket_name in bucket_names:
                    logger.info(f"✅ Bucket '{self.bucket_name}' hittad")
                    return True
                else:
                    logger.error(f"❌ Bucket '{self.bucket_name}' inte hittad. Tillgängliga: {bucket_names}")
                    return False
            else:
                logger.error(f"Connection test failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


def main():
    """
    Test av uploader
    """
    print("=== CLOUDFLARE R2 UPLOADER TEST ===\n")
    
    try:
        uploader = CloudflareUploader()
        
        # Test anslutning
        print("📋 Testar anslutning...")
        if not uploader.test_connection():
            print("❌ Anslutningstest misslyckades")
            return
        
        # Lista objekt
        print("\n📋 Listar befintliga objekt...")
        objects = uploader.list_objects()
        for obj in objects[:3]:  # Visa bara första 3
            print(f"   - {obj.get('key', 'Unknown')} ({obj.get('size', 0)} bytes)")
        
        # Skapa test-fil
        print("\n📋 Skapar test-fil...")
        test_file = "upload_test.json"
        test_data = {
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "uploader": "bearer_token_v3"
        }
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f, indent=2)
        
        # Upload test
        print(f"\n📋 Laddar upp {test_file}...")
        result_url = uploader.upload_file(test_file)
        
        if result_url:
            print("✅ Upload lyckades!")
            print(f"   Public URL: {result_url}")
        else:
            print("❌ Upload misslyckades")
        
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
            
    except Exception as e:
        print(f"❌ Test misslyckades: {e}")


if __name__ == "__main__":
    main()
