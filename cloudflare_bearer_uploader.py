#!/usr/bin/env python3
"""
Cloudflare R2 Uploader som använder Account API Token (Bearer authentication)
"""

import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

class CloudflareBearerUploader:
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
        
        print(f"✅ Bearer Uploader initialiserad")
        print(f"   Account ID: {self.account_id}")
        print(f"   Bucket: {self.bucket_name}")
        print(f"   Public URL: {self.public_url}")

    def upload_file(self, file_path, object_key=None):
        """
        Ladda upp fil till R2 med Bearer token authentication
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if object_key is None:
                object_key = os.path.basename(file_path)
            
            # Läs fil
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Cloudflare R2 API endpoint för file upload
            url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/r2/buckets/{self.bucket_name}/objects/{object_key}"
            
            # Upload headers för binär data
            upload_headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/octet-stream'
            }
            
            print(f"📤 Laddar upp {file_path} som {object_key}...")
            
            response = requests.put(url, data=file_data, headers=upload_headers)
            
            if response.status_code in [200, 201, 204]:
                print(f"✅ Upload lyckades!")
                public_file_url = f"{self.public_url}/{object_key}"
                print(f"   Public URL: {public_file_url}")
                return {
                    'success': True,
                    'object_key': object_key,
                    'public_url': public_file_url
                }
            else:
                print(f"❌ Upload misslyckades: {response.status_code}")
                print(f"   Response: {response.text}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def list_objects(self):
        """
        Lista objekt i bucket
        """
        try:
            url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/r2/buckets/{self.bucket_name}/objects"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                objects = data.get('result', {}).get('objects', [])
                print(f"✅ Hittade {len(objects)} objekt i bucket")
                for obj in objects[:5]:  # Visa bara första 5
                    print(f"   - {obj.get('key', 'Unknown')} ({obj.get('size', 0)} bytes)")
                return objects
            else:
                print(f"❌ List misslyckades: {response.status_code}")
                print(f"   Response: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ List error: {e}")
            return []

    def test_connection(self):
        """
        Testa anslutning genom att lista buckets
        """
        try:
            # Lista buckets för att testa anslutning
            url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/r2/buckets"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                buckets = data.get('result', {}).get('buckets', [])
                print(f"✅ Anslutning lyckades! Hittade {len(buckets)} buckets")
                for bucket in buckets:
                    print(f"   - {bucket.get('name', 'Unknown')}")
                return True
            else:
                print(f"❌ Anslutning misslyckades: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False

def main():
    """
    Test av Bearer token uploader
    """
    print("=== CLOUDFLARE R2 BEARER TOKEN TEST ===\n")
    
    try:
        uploader = CloudflareBearerUploader()
        
        print("\n📋 Test 1: Testa anslutning...")
        if not uploader.test_connection():
            print("❌ Anslutningstest misslyckades")
            return
        
        print("\n📋 Test 2: Lista objekt...")
        uploader.list_objects()
        
        print("\n📋 Test 3: Skapa test-fil...")
        test_file = "bearer_test.json"
        test_data = {
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "method": "bearer_token"
        }
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f, indent=2)
        
        print(f"   Skapade {test_file}")
        
        print("\n📋 Test 4: Upload test-fil...")
        result = uploader.upload_file(test_file)
        
        if result['success']:
            print("✅ Alla tester lyckades!")
        else:
            print(f"❌ Upload misslyckades: {result['error']}")
        
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
            
    except Exception as e:
        print(f"❌ Test misslyckades: {e}")

if __name__ == "__main__":
    main()
