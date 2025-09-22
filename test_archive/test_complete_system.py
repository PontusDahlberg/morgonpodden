#!/usr/bin/env python3
"""
Komplett test av podcast-generering lokalt
Testar hela kedjan: nyheter → AI-sammanfattning → audio → upload
"""

import os
import sys
from dotenv import load_dotenv

# Ladda miljövariabler
load_dotenv()

def test_environment():
    """Testa att alla API-nycklar finns"""
    print("🔧 Testar miljövariabler...")
    
    required_vars = [
        'OPENROUTER_API_KEY',
        'ELEVENLABS_API_KEY', 
        'ELEVENLABS_VOICE_ID',
        'CLOUDFLARE_API_TOKEN',
        'CLOUDFLARE_R2_BUCKET',
        'CLOUDFLARE_R2_PUBLIC_URL'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
        else:
            print(f"✅ {var}: OK")
    
    if missing:
        print(f"❌ Saknas: {', '.join(missing)}")
        return False
    
    print("✅ Alla miljövariabler OK!")
    return True

def test_openrouter():
    """Testa OpenRouter API"""
    print("\n🤖 Testar OpenRouter API...")
    
    try:
        import requests
        
        api_key = os.getenv('OPENROUTER_API_KEY')
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'anthropic/claude-3.5-sonnet',
            'messages': [{'role': 'user', 'content': 'Säg hej på svenska'}],
            'max_tokens': 50
        }
        
        response = requests.post('https://openrouter.ai/api/v1/chat/completions', 
                               headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content']
            print(f"✅ OpenRouter fungerar! Svar: {answer[:50]}...")
            return True
        else:
            print(f"❌ OpenRouter fel: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ OpenRouter error: {e}")
        return False

def test_elevenlabs():
    """Testa ElevenLabs API"""
    print("\n🎵 Testar ElevenLabs API...")
    
    try:
        import requests
        
        api_key = os.getenv('ELEVENLABS_API_KEY')
        voice_id = os.getenv('ELEVENLABS_VOICE_ID')
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        data = {
            "text": "Detta är ett test av ljudgenerering för Människa Maskin Miljö.",
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            # Spara testfil
            os.makedirs('audio', exist_ok=True)
            with open('audio/test_local.mp3', 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content)
            print(f"✅ ElevenLabs fungerar! Audio: audio/test_local.mp3 ({file_size} bytes)")
            return True
        else:
            print(f"❌ ElevenLabs fel: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ElevenLabs error: {e}")
        return False

def test_cloudflare():
    """Testa Cloudflare R2 API"""
    print("\n☁️ Testar Cloudflare R2...")
    
    try:
        import requests
        
        token = os.getenv('CLOUDFLARE_API_TOKEN')
        account_id = '9c5323b560f65e0ead7cee1bdba8a690'
        
        headers = {'Authorization': f'Bearer {token}'}
        url = f'https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets'
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            buckets = response.json()
            bucket_names = [b['name'] for b in buckets.get('result', [])]
            print(f"✅ Cloudflare fungerar! Buckets: {bucket_names}")
            return True
        else:
            print(f"❌ Cloudflare fel: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Cloudflare error: {e}")
        return False

def test_full_pipeline():
    """Testa hela podcast-pipeline"""
    print("\n🎙️ Testar fullständig podcast-generering...")
    
    try:
        # Importera huvudfunktionen
        from run_podcast import main as run_podcast_main
        
        print("Kör run_podcast.py...")
        result = run_podcast_main()
        
        if result:
            print("✅ Fullständig podcast-generering lyckades!")
            return True
        else:
            print("❌ Podcast-generering misslyckades")
            return False
            
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        return False

def main():
    """Huvudtest-funktion"""
    print("🧪 KOMPLETT LOKALT TEST - Människa Maskin Miljö")
    print("=" * 60)
    
    tests = [
        ("Miljövariabler", test_environment),
        ("OpenRouter API", test_openrouter),
        ("ElevenLabs API", test_elevenlabs),
        ("Cloudflare R2", test_cloudflare),
        ("Full Pipeline", test_full_pipeline)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} kraschade: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 TESTRESULTAT:")
    print()
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if not success:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 ALLA TESTER PASSERADE!")
        print("Systemet är redo för GitHub Actions deployment!")
    else:
        print("⚠️ NÅGRA TESTER MISSLYCKADES")
        print("Fixa problemen innan GitHub deployment.")
    
    return all_passed

if __name__ == "__main__":
    main()
