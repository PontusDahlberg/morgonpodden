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
        
        try:
            with open(local_path, 'rb') as f:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=remote_path,
                    Body=f,
                    ContentType=content_type,
                    CacheControl='public, max-age=3600'
                )
            
            public_url = f"{self.public_url}/{remote_path}"
            logger.info(f"Uploaded {local_path} to {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"Upload failed for {local_path}: {e}")
            raise
    
    def upload_episode(self, audio_file: str, metadata: Dict) -> Dict:
        """Upload an episode and its metadata"""
        episode_number = metadata['episode_number']
        
        # Upload audio file
        audio_remote = f"episodes/episode_{episode_number}.mp3"
        audio_url = self.upload_file(audio_file, audio_remote)
        
        # Update metadata with public URL
        metadata['audio_url'] = audio_url
        metadata['uploaded_at'] = datetime.now().isoformat()
        
        # Save and upload metadata
        meta_file = f"episodes/episode_{episode_number}_meta.json"
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        meta_remote = f"episodes/episode_{episode_number}_meta.json"
        self.upload_file(meta_file, meta_remote)
        
        return metadata
    
    def upload_feed(self, feed_file: str = 'public/feed.xml'):
        """Upload RSS feed"""
        self.upload_file(feed_file, 'feed.xml')
        
        # Also upload the JSON version if it exists
        json_file = feed_file.replace('.xml', '.json')
        if os.path.exists(json_file):
            self.upload_file(json_file, 'feed.json')
    
    def upload_static_files(self):
        """Upload static files like images and HTML"""
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
                self.upload_file(local, remote)
                logger.info(f"Uploaded static file: {local} -> {remote}")
            else:
                logger.warning(f"Static file not found: {local}")
    
    def sync_all_episodes(self):
        """Sync all local episodes to Cloudflare R2"""
        episodes_dir = 'episodes'
        if not os.path.exists(episodes_dir):
            logger.warning("No episodes directory found")
            return
        
        # Find all audio files
        audio_files = [f for f in os.listdir(episodes_dir) if f.endswith('.mp3')]
        
        for audio_file in audio_files:
            audio_path = os.path.join(episodes_dir, audio_file)
            
            # Find corresponding metadata
            meta_file = audio_file.replace('.mp3', '_metadata.json')
            meta_path = os.path.join(episodes_dir, meta_file)
            
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Upload episode
                self.upload_episode(audio_path, metadata)
        
        logger.info(f"Synced {len(audio_files)} episodes to Cloudflare R2")

def main():
    uploader = CloudflareUploader()
    
    # Upload latest episode if it exists
    episodes_dir = 'episodes'
    if os.path.exists(episodes_dir):
        audio_files = [f for f in os.listdir(episodes_dir) if f.endswith('.mp3')]
        if audio_files:
            latest = max(audio_files, key=lambda x: os.path.getctime(os.path.join(episodes_dir, x)))
            audio_path = os.path.join(episodes_dir, latest)
            
            # Load metadata
            meta_file = latest.replace('.mp3', '_metadata.json')
            meta_path = os.path.join(episodes_dir, meta_file)
            
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Upload episode
                uploader.upload_episode(audio_path, metadata)
    
    # Upload feed
    if os.path.exists('public/feed.xml'):
        uploader.upload_feed()
    
    # Upload static files
    uploader.upload_static_files()
    
    logger.info("Upload completed")

if __name__ == "__main__":
    main()