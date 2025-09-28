#!/usr/bin/env python3
"""
Quick API test to verify credentials work
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openrouter():
    """Test OpenRouter API"""
    import requests
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OpenRouter API key missing")
        return False
        
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        if response.status_code == 200:
            models = response.json()
            print(f"✅ OpenRouter: {len(models.get('data', []))} modeller tillgängliga")
            return True
        else:
            print(f"❌ OpenRouter: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ OpenRouter error: {e}")
        return False

def test_elevenlabs():
    """Test ElevenLabs API"""
    import requests
    
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("❌ ElevenLabs API key missing")
        return False
        
    try:
        response = requests.get(
            "https://api.elevenlabs.io/v1/user",
            headers={"xi-api-key": api_key}
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ ElevenLabs: Användare verifierad")
            return True
        else:
            print(f"❌ ElevenLabs: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ElevenLabs error: {e}")
        return False

def test_cloudflare():
    """Test Cloudflare R2 API"""
    import requests
    
    api_token = os.getenv('CLOUDFLARE_API_TOKEN')
    account_id = os.getenv('CLOUDFLARE_R2_ACCOUNT_ID')
    
    if not api_token or not account_id:
        print("❌ Cloudflare credentials missing")
        return False
        
    try:
        response = requests.get(
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets",
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            buckets = response.json()
            print(f"✅ Cloudflare R2: {len(buckets.get('result', []))} buckets tillgängliga")
            return True
        else:
            print(f"❌ Cloudflare: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Cloudflare error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 API CREDENTIALS TEST")
    print("=" * 30)
    
    results = []
    results.append(("OpenRouter", test_openrouter()))
    results.append(("ElevenLabs", test_elevenlabs()))
    results.append(("Cloudflare R2", test_cloudflare()))
    
    print("\n📊 RESULTAT:")
    print("=" * 30)
    for service, success in results:
        status = "✅ OK" if success else "❌ FAIL"
        print(f"{service:15} {status}")
        
    all_good = all(result[1] for result in results)
    print(f"\n🎯 Övergripande status: {'✅ ALLA TJÄNSTER OK' if all_good else '⚠️ VISSA PROBLEM'}")
    
    if all_good:
        print("\n🚀 Systemet är redo för podcast-generering!")
        print("Kör: python run_podcast.py")
    else:
        print("\n🔧 Åtgärda API-problem innan podcast-generering")