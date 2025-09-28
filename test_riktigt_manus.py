#!/usr/bin/env python3
"""
Test av det riktiga gamla manuset med Google Cloud TTS
"""

import os
import sys
import re
sys.path.append('.')

from google_tts_backup import create_google_podcast_service_account

def test_riktigt_manus():
    """Testar det gamla manuset med Google Cloud TTS"""
    
    # Sätt upp credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-service-account.json'
    
    script_file = "scripts/podcast_script_20250920_180259.txt"
    
    if not os.path.exists(script_file):
        print(f"❌ Manusfil saknas: {script_file}")
        return None
    
    # Läs och extrahera första delen av manuset
    try:
        with open(script_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extrahera första 10 dialog-segmenten
        segments = []
        dialog_pattern = r'(Anna|Erik):\s*\[?([^\]]*?)\]?\s*(.+?)(?=\n(?:Anna|Erik|\[MUSIK|$))'
        matches = re.findall(dialog_pattern, content, re.DOTALL)
        
        for speaker, style, text in matches[:8]:  # Första 8 segmenten
            voice = "lisa" if speaker == "Anna" else "pelle"
            
            # Två versioner - med och utan style
            original_text = f"[{style}] {text}".strip() if style else text.strip()
            clean_text = text.strip()
            
            # Använd originalet med style-taggar för detta test
            segments.append({
                "voice": voice,
                "text": original_text[:200] + "..." if len(original_text) > 200 else original_text
            })
        
        print("🎙️ TESTAR: Riktigt manus från september med Google Cloud TTS")
        print("=" * 65)
        print(f"📅 Original manus: {script_file}")
        print(f"🎤 Testar första {len(segments)} segment")
        print("\n📝 SEGMENT:")
        for i, seg in enumerate(segments, 1):
            style_info = "MED STYLE" if "[" in seg["text"] else "UTAN STYLE"
            print(f"   {i}. {seg['voice']} ({style_info}): {seg['text'][:50]}...")
        print()
        
        # Skapa podcast med segmenten  
        result = create_google_podcast_service_account(segments)
        
        if result:
            print(f"\n✅ RIKTIGT MANUS TEST: {result}")
            print("\n🎧 LYSSNINGSTEST:")
            print("   🎭 Läser Google upp style-taggarna som '[friendly]'?")
            print("   🎶 Hur låter det jämfört med ElevenLabs-versionen?")
            print("   🗣️ Fungerar Lisa och Pelle som Anna och Erik?")
            print("\n💰 KOSTNADSJÄMFÖRELSE:")
            print("   • Detta test ~$0.01 med Google Cloud")
            print("   • Samma längd ~$0.15 med ElevenLabs")
            print("   • 15x billigare med Google!")
            
            return result
        else:
            print("\n❌ Kunde inte skapa test")
            return None
            
    except Exception as e:
        print(f"❌ Fel vid läsning: {e}")
        return None

if __name__ == "__main__":
    test_riktigt_manus()