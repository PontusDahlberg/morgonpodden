#!/usr/bin/env python3
"""
Test ny Cloudflare token
"""

import os
from dotenv import load_dotenv
import requests

load_dotenv()

def test_cloudflare_token():
    api_token = os.getenv('CLOUDFLARE_API_TOKEN')
    account_id = '9c5323b560f65e0ead7cee1bdba8a690'

    print('🔍 Testar nya Cloudflare token...')
    print(f'Token: {api_token[:20] if api_token else "MISSING"}...')

    if not api_token:
        print('❌ CLOUDFLARE_API_TOKEN not found in .env')
        return False

    headers = {'Authorization': f'Bearer {api_token}'}
    url = f'https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets'

    try:
        response = requests.get(url, headers=headers)
        print(f'Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            buckets = data.get('result', {}).get('buckets', [])
            print(f'✅ Nya token fungerar! Hittade {len(buckets)} buckets')
            for bucket in buckets:
                name = bucket.get('name', 'Unknown')
                print(f'   - {name}')
            return True
        else:
            print(f'❌ Token error: {response.text}')
            return False
            
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

if __name__ == "__main__":
    test_cloudflare_token()
