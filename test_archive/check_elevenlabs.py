#!/usr/bin/env python3
"""
ElevenLabs Status Checker
"""

import os
from dotenv import load_dotenv
import requests

load_dotenv()

def check_elevenlabs_status():
    api_key = os.getenv('ELEVENLABS_API_KEY')
    voice_id = os.getenv('ELEVENLABS_VOICE_ID')

    print('🔍 Kollar ElevenLabs status...')
    print(f'API Key: {api_key[:20] if api_key else "Missing"}...')
    print(f'Voice ID: {voice_id}')

    if not api_key:
        print('❌ ELEVENLABS_API_KEY saknas!')
        return False

    # Kolla användning/credits
    url = 'https://api.elevenlabs.io/v1/user'
    headers = {'xi-api-key': api_key}

    try:
        response = requests.get(url, headers=headers)
        print(f'Status Code: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print('✅ ElevenLabs API fungerar!')
            
            subscription = data.get('subscription', {})
            character_count = subscription.get('character_count', 0)
            character_limit = subscription.get('character_limit', 0)
            tier = subscription.get('tier', 'N/A')
            
            print(f'📊 Credits: {character_count}/{character_limit} tecken')
            print(f'👤 Subscription: {tier}')
            
            if character_count > 0:
                print('🎉 Du har credits! ElevenLabs är redo att använda!')
                return True
            else:
                print('⚠️ Inga credits tillgängliga än')
                return False
                
        else:
            print(f'❌ API Error: {response.text}')
            return False
            
    except Exception as e:
        print(f'❌ Connection Error: {e}')
        return False

if __name__ == "__main__":
    check_elevenlabs_status()
