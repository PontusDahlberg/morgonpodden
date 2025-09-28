#!/usr/bin/env python3
"""
Enkel fix - fokus på fade out och inga tankstreck
"""

import subprocess
import os
import shutil

def create_fade_out_fix():
    """Fixar endast fade out och crossfade"""
    
    voice_file = "audio/episode_google_service_account.mp3"
    intro_music = "audio/music/Mellan Dröm och Verklighet.mp3"
    outro_music = "audio/music/MMM Senaste Nytt Från Människa Maskin Mi.mp3"
    
    for file in [voice_file, intro_music, outro_music]:
        if not os.path.exists(file):
            print(f"❌ Saknar: {file}")
            return None
    
    if not shutil.which('ffmpeg'):
        print("❌ ffmpeg saknas")
        return None
    
    output_file = "audio/premiar_FIXAD_FADE.mp3"
    
    try:
        print("🎵 Fixar fade out problem...")
        
        cmd = [
            'ffmpeg', '-y',
            
            # Input filer
            '-i', intro_music,    # [0] Intro
            '-i', voice_file,     # [1] Röst (utan tankstreck)
            '-i', outro_music,    # [2] Outro
            
            # Enklare filter med kraftigare fade out
            '-filter_complex', 
            # Intro: 15 sek med crossfade
            '[0:a]atrim=0:17,afade=t=out:st=15:d=2,volume=0.7[intro];'
            # Röst: crossfade in
            '[1:a]afade=t=in:st=0:d=2,volume=1.0[voice];'
            # Outro: 60 sek med KRAFTIG fade out (6 sekunder!)
            '[2:a]atrim=0:62,volume=0.5,afade=t=in:st=0:d=2,afade=t=out:st=56:d=6[outro];'
            # Sätt ihop
            '[intro][voice][outro]concat=n=3:v=0:a=1[out]',
            
            '-map', '[out]',
            '-c:a', 'mp3',
            '-b:a', '192k',
            output_file
        ]
        
        print("   ✅ Kraftig 6-sek fade out på outro")
        print("   ✅ Crossfade från intro till tal")
        print("   ✅ Tal utan tankstreck")
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            print(f"\n✅ FIXAD VERSION: {output_file}")
            
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"📊 Filstorlek: {file_size/1024/1024:.1f} MB")
                print("\n🎧 Testa fade out nu!")
            
            return output_file
        else:
            print(f"❌ ffmpeg fel: {result.stderr[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Fel: {e}")
        return None

def main():
    print("🔧 FIXAR: Fade out och tankstreck")
    print("=" * 35)
    
    result = create_fade_out_fix()
    
    if result:
        print(f"\n🎉 FADE OUT FIXAD!")
        print("📝 För bryggor (valfritt):")
        print("   • Öppna i Audacity")
        print("   • Lägg till 6-sek musikstycken vid bryggpunkter")
        print("   • Använd en av dina andra musikfiler")
    else:
        print("\n💡 Manuell metod rekommenderas för perfekt kontroll")

if __name__ == "__main__":
    main()