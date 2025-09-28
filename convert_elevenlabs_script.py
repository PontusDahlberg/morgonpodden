#!/usr/bin/env python3
"""
Verktyg för att konvertera ElevenLabs-manus till Google Cloud TTS format
"""

import re
import os

def clean_elevenlabs_script(input_file, output_file=None):
    """Rensar style-taggar från ElevenLabs-manus"""
    
    if not os.path.exists(input_file):
        print(f"❌ Kan inte hitta fil: {input_file}")
        return None
    
    if output_file is None:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_GOOGLE_CLEAN.txt"
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📄 Läser manus: {input_file}")
        
        # Räkna style-taggar innan rensning
        style_pattern = r'\[([^\]]+)\]'
        styles_found = re.findall(style_pattern, content)
        unique_styles = set(styles_found)
        
        print(f"🎭 Hittade {len(styles_found)} style-taggar:")
        for style in sorted(unique_styles):
            count = styles_found.count(style) 
            print(f"   • [{style}]: {count} gånger")
        
        # Rensa bort style-taggar
        cleaned_content = re.sub(style_pattern, '', content)
        
        # Ta bort extra whitespace som kan ha blivit kvar
        cleaned_content = re.sub(r'\s+', ' ', cleaned_content)
        cleaned_content = re.sub(r'^\s+', '', cleaned_content, flags=re.MULTILINE)
        
        # Spara rensad version
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print(f"\n✅ Rensat manus sparat: {output_file}")
        print(f"📊 Reducerat från {len(content)} till {len(cleaned_content)} tecken")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Fel vid rensning: {e}")
        return None

def extract_segments_for_google_tts(script_file):
    """Extraherar segment från manuset för Google TTS"""
    
    if not os.path.exists(script_file):
        print(f"❌ Manusfil saknas: {script_file}")
        return None
    
    try:
        with open(script_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extrahera Anna/Erik-segment
        segments = []
        
        # Enkel regex för att hitta dialog-rader
        dialog_pattern = r'(Anna|Erik):\s*(.+?)(?=\n(?:Anna|Erik|$|\[MUSIK))'
        matches = re.findall(dialog_pattern, content, re.DOTALL)
        
        for speaker, text in matches:
            # Rensa style-taggar
            clean_text = re.sub(r'\[([^\]]+)\]', '', text).strip()
            
            # Mappa till våra röster
            voice = "lisa" if speaker == "Anna" else "pelle"
            
            if clean_text:  # Bara om det finns text kvar
                segments.append({
                    "voice": voice,
                    "text": clean_text
                })
        
        print(f"📝 Extraherade {len(segments)} dialog-segment")
        return segments
        
    except Exception as e:
        print(f"❌ Fel vid extraktion: {e}")
        return None

def main():
    script_file = "scripts/podcast_script_20250920_180259.txt"
    
    print("🔧 ELEVENLABS → GOOGLE CLOUD TTS KONVERTERING")
    print("=" * 55)
    
    # Steg 1: Rensa style-taggar
    cleaned_file = clean_elevenlabs_script(script_file)
    
    if cleaned_file:
        print(f"\n📁 RESULTAT:")
        print(f"   Original: {script_file}")  
        print(f"   Rensad:   {cleaned_file}")
        print("\n💡 NÄSTA STEG:")
        print("   1. Lyssna på style-testet först")
        print("   2. Om Google läser upp taggarna - använd den rensade filen")
        print("   3. Om Google ignorerar taggarna - använd originalet")
    
    # Steg 2: Extrahera segment för Google TTS test
    segments = extract_segments_for_google_tts(script_file)
    
    if segments and len(segments) > 0:
        print(f"\n🎤 FÖRSTA 3 SEGMENT för test:")
        for i, seg in enumerate(segments[:3], 1):
            print(f"   {i}. {seg['voice']}: {seg['text'][:60]}...")

if __name__ == "__main__":
    main()