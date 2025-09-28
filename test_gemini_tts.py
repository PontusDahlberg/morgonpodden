#!/usr/bin/env python3
"""
Test av Gemini TTS API som backup till ElevenLabs
"""

import os
import requests
import json
from typing import Dict, Any

def test_gemini_tts():
    """Testa Gemini TTS capabilities"""
    
    # Första test: kolla vilka röster som finns tillgängliga
    print("🔍 Kollar Gemini TTS-röster...")
    
    # Du behöver sätta din Gemini API key
    api_key = os.getenv('GEMINI_API_KEY')  # Lägg till din nyckel här
    
    if not api_key:
        print("⚠️ GEMINI_API_KEY saknas i miljövariabler")
        print("Lägg till din Gemini API-nyckel i .env filen:")
        print("GEMINI_API_KEY=your_gemini_api_key_here")
        return
    
    # Testa grundläggande TTS
    test_text = "Hej och välkommen till Människa Maskin Miljö! Detta är en test av Gemini TTS."
    
    try:
        # Gemini AI Studio kan inte göra TTS direkt
        # Men vi kan använda Google Cloud Text-to-Speech med Gemini för textgenerering
        
        # Alternativ 1: Google Cloud TTS (kräver Google Cloud setup)
        # Alternativ 2: Använda andra TTS-tjänster som backup
        
        print("🤔 Gemini AI Studio har ingen direkt TTS-funktion")
        print("Förslag på backup-TTS alternativ:")
        print("1. Google Cloud Text-to-Speech (kräver Google Cloud konto)")
        print("2. Azure Cognitive Services Speech")
        print("3. AWS Polly")
        print("4. OpenAI TTS (billigare än ElevenLabs)")
        
        # Testa OpenAI TTS istället?
        return test_openai_tts()
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_openai_tts():
    """Testa OpenAI TTS som backup"""
    print("\n🎯 Testar OpenAI TTS som backup...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️ OPENAI_API_KEY saknas")
        return
    
    url = "https://api.openai.com/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # OpenAI TTS har svenska stöd och är mycket billigare än ElevenLabs
    data = {
        "model": "tts-1",  # eller tts-1-hd för högre kvalitet
        "input": "Hej och välkommen till Människa Maskin Miljö! Detta är en test av OpenAI TTS.",
        "voice": "nova"  # alloy, echo, fable, onyx, nova, shimmer
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ OpenAI TTS fungerar!")
            with open('audio/test_openai.mp3', 'wb') as f:
                f.write(response.content)
            print(f"🎵 Test-audio sparad: audio/test_openai.mp3 ({len(response.content)} bytes)")
            return True
        else:
            print(f"❌ Fel: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def list_available_voices():
    """Lista tillgängliga svenska röster"""
    print("\n🎭 Tillgängliga svenska röster i Google Cloud TTS:")
    
    voices = [
        {"name": "sv-SE-Standard-A", "gender": "FEMALE", "description": "Standard kvinnlig röst"},
        {"name": "sv-SE-Standard-B", "gender": "MALE", "description": "Standard manlig röst"},
        {"name": "sv-SE-Standard-C", "gender": "FEMALE", "description": "Standard kvinnlig röst (alt)"},
        {"name": "sv-SE-Standard-D", "gender": "MALE", "description": "Standard manlig röst (alt)"},
        {"name": "sv-SE-Wavenet-A", "gender": "FEMALE", "description": "WaveNet kvinnlig röst (högre kvalitet)"},
        {"name": "sv-SE-Wavenet-B", "gender": "MALE", "description": "WaveNet manlig röst (högre kvalitet)"},
        {"name": "sv-SE-Wavenet-C", "gender": "FEMALE", "description": "WaveNet kvinnlig röst (alt)"},
    ]
    
    for voice in voices:
        print(f"  • {voice['name']} ({voice['gender']}): {voice['description']}")

if __name__ == "__main__":
    print("🤖 Testar TTS-alternativ som backup för ElevenLabs")
    print("=" * 60)
    
    print("💡 Kostnadsanalys:")
    print("• ElevenLabs: ~$0.18 per 1000 tecken (Starter)")
    print("• OpenAI TTS: $0.015 per 1000 tecken (12x billigare!)")
    print("• Google Cloud: $4 per 1 miljon tecken (mycket billigare)")
    print()
    
    list_available_voices()
    test_gemini_tts()
