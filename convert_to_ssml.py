#!/usr/bin/env python3
"""
Konverterar ElevenLabs-styles till Google Cloud SSML
"""

import re
import os

def convert_styles_to_ssml(text):
    """Konverterar [style]-taggar till SSML"""
    
    # Mapping från ElevenLabs styles till SSML
    style_mappings = {
        # Positiva känslor - högre tonhöjd, snabbare tempo
        'excited': '<prosody rate="fast" pitch="+4st" volume="loud">',
        'happy': '<prosody rate="medium" pitch="+3st" volume="medium">',
        'friendly': '<prosody rate="medium" pitch="+1st" volume="medium">',
        'warm': '<prosody rate="slow" pitch="+2st" volume="soft">',
        
        # Nyfikenhet/intresse - varierande tonhöjd
        'curious': '<prosody rate="medium" pitch="+2st">',
        'interested': '<prosody rate="medium" pitch="+1st">',
        'surprised': '<prosody rate="fast" pitch="+5st" volume="loud">',
        
        # Seriösa känslor - lägre tonhöjd, långsammare
        'concerned': '<prosody rate="slow" pitch="-2st" volume="soft">',
        'serious': '<prosody rate="slow" pitch="-1st" volume="medium">',
        'thoughtful': '<prosody rate="slow" pitch="0st">',
        'neutral': '<prosody rate="medium" pitch="0st" volume="medium">',
        
        # Negativa känslor
        'worried': '<prosody rate="slow" pitch="-3st" volume="soft">',
        'sad': '<prosody rate="slow" pitch="-4st" volume="soft">',
        
        # Speciella
        'laughing': '<prosody rate="fast" pitch="+3st" volume="loud">Haha! ',
        'smiling': '<prosody rate="medium" pitch="+2st">',
        'amused': '<prosody rate="medium" pitch="+1st">',
        'impressed': '<prosody rate="medium" pitch="+2st"><emphasis level="moderate">',
        
        # Tonfalls-modifierare som läggs till emphasis
        'emphasis': '<emphasis level="strong">',
        'moderate': '<emphasis level="moderate">',
        'strong': '<emphasis level="strong">',
    }
    
    def replace_style(match):
        style = match.group(1).lower()
        if style in style_mappings:
            return style_mappings[style]
        else:
            # Okänd style - använd neutral
            return '<prosody rate="medium" pitch="0st">'
    
    # Ersätt [style] med SSML
    ssml_text = re.sub(r'\[([^\]]+)\]', replace_style, text)
    
    # Lägg till avslutande taggar för öppnade prosody-taggar
    prosody_count = ssml_text.count('<prosody')
    emphasis_count = ssml_text.count('<emphasis')
    
    # Lägg till avslutande taggar i slutet av texten
    for _ in range(emphasis_count):
        ssml_text += '</emphasis>'
    for _ in range(prosody_count):
        ssml_text += '</prosody>'
    
    return ssml_text

def convert_script_to_ssml(input_file, output_file=None):
    """Konverterar hela manuset till SSML-format"""
    
    if not os.path.exists(input_file):
        print(f"❌ Fil saknas: {input_file}")
        return None
    
    if output_file is None:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_SSML.txt"
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📄 Konverterar: {input_file}")
        
        # Hitta alla styles före konvertering
        style_pattern = r'\[([^\]]+)\]'
        styles_found = re.findall(style_pattern, content)
        unique_styles = set(s for s in styles_found if not s.startswith('MUSIK'))
        
        print(f"🎭 Konverterar {len(unique_styles)} olika styles:")
        for style in sorted(unique_styles):
            print(f"   • [{style}] → SSML")
        
        # Konvertera text rad för rad för bättre kontroll
        lines = content.split('\n')
        converted_lines = []
        
        for line in lines:
            if ':' in line and ('Anna:' in line or 'Erik:' in line):
                # Detta är en dialog-rad
                parts = line.split(':', 1)
                if len(parts) == 2:
                    speaker = parts[0].strip()
                    dialogue = parts[1].strip()
                    
                    # Konvertera styles i dialogen
                    ssml_dialogue = convert_styles_to_ssml(dialogue)
                    
                    # Wrappa i SSML speak-taggar
                    full_ssml = f"{speaker}: <speak>{ssml_dialogue}</speak>"
                    converted_lines.append(full_ssml)
                else:
                    converted_lines.append(line)
            else:
                # Behold övrig text (rubriker, instruktioner etc)
                converted_lines.append(line)
        
        converted_content = '\n'.join(converted_lines)
        
        # Spara konverterad version
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(converted_content)
        
        print(f"\n✅ SSML-version sparad: {output_file}")
        print(f"📊 {len(content)} → {len(converted_content)} tecken")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Konverteringsfel: {e}")
        return None

def main():
    script_file = "scripts/podcast_script_20250920_180259.txt"
    
    print("🔄 ELEVENLABS STYLES → GOOGLE SSML KONVERTERING")
    print("=" * 55)
    
    # Test av enskild konvertering
    test_text = "[excited] Det här är fantastiska nyheter! [curious] Vad tror du om det?"
    ssml_result = convert_styles_to_ssml(test_text)
    
    print("🧪 TEST-KONVERTERING:")
    print(f"   IN:  {test_text}")
    print(f"   OUT: <speak>{ssml_result}</speak>")
    print()
    
    # Konvertera hela manuset
    if os.path.exists(script_file):
        result = convert_script_to_ssml(script_file)
        
        if result:
            print("\n💡 NÄSTA STEG:")
            print("   1. Testa WaveNet SSML-filerna först")
            print("   2. Om kvaliteten är acceptabel, använd SSML-versionen")
            print("   3. Jämför kostnad: WaveNet (4x dyrare) vs Chirp3-HD")
    else:
        print(f"❌ Manusfil saknas: {script_file}")

if __name__ == "__main__":
    main()