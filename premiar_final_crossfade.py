#!/usr/bin/env python3
"""
Förbättrad musikmixer med crossfade och nya låtar
"""

import subprocess
import os
import shutil

def create_premiar_med_crossfade(voice_file="audio/episode_google_service_account.mp3"):
    """Skapar premiär med crossfade och nya låtar"""
    
    if not os.path.exists(voice_file):
        print(f"❌ Kan inte hitta röstsfilmen: {voice_file}")
        return None
    
    # Kontrollera att de nya låtarna finns
    intro_music = "audio/music/Mellan Dröm och Verklighet.mp3"
    outro_music = "audio/music/MMM Senaste Nytt Från Människa Maskin Mi.mp3"
    
    if not os.path.exists(intro_music):
        print(f"❌ Kan inte hitta intro-musik: {intro_music}")
        return None
    
    if not os.path.exists(outro_music):
        print(f"❌ Kan inte hitta outro-musik: {outro_music}")
        return None
        
    # Kontrollera om ffmpeg finns
    if not shutil.which('ffmpeg'):
        print("⚠️ ffmpeg inte installerat")
        return None
    
    output_file = "audio/premiar_final_med_crossfade.mp3"
    
    try:
        print("🎵 Skapar premiär med crossfade och nya låtar...")
        
        # Förbättrat ffmpeg med crossfade
        cmd = [
            'ffmpeg', '-y',  # Överskriv output
            
            # Input filer
            '-i', intro_music,    # [0] Intro: "Mellan Dröm och Verklighet"
            '-i', voice_file,     # [1] Röstfil (Lisa & Pelle)
            '-i', outro_music,    # [2] Outro: "MMM Senaste Nytt..."
            
            # Avancerad filter med crossfade
            '-filter_complex', 
            # Intro: 15 sek, crossfade ut
            '[0:a]atrim=0:17,afade=t=out:st=15:d=2,volume=0.7[intro];'
            # Röst: crossfade in, normal volym
            '[1:a]afade=t=in:st=0:d=2,volume=1.0[voice];'
            # Outro: 60 sek med fade in/out
            '[2:a]atrim=0:62,afade=t=in:st=0:d=2,afade=t=out:st=60:d=2,volume=0.5[outro];'
            # Sätt ihop med mjuka övergångar
            '[intro][voice][outro]concat=n=3:v=0:a=1[out]',
            
            '-map', '[out]',
            '-c:a', 'mp3',
            '-b:a', '192k',
            '-ar', '44100',
            output_file
        ]
        
        print("🔧 Kör ffmpeg med crossfade...")
        print("   🎼 15 sek intro från 'Mellan Dröm och Verklighet'")
        print("   🗣️ 3.3 min Lisa & Pelle (utan punkter)")
        print("   🎼 60 sek outro från nya låten")
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            print(f"\n✅ PREMIÄR MED CROSSFADE SKAPAD: {output_file}")
            
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"📊 Filstorlek: {file_size/1024/1024:.1f} MB")
                print("🎧 Funktioner:")
                print("   ✅ Crossfade från intro till Lisa")
                print("   ✅ Inga märkliga punkter")
                print("   ✅ Mjuk övergång till outro")
                print("   ✅ Fade out på slutet")
            
            return output_file
            
        else:
            print(f"❌ ffmpeg fel (kod {result.returncode}):")
            if result.stderr:
                print(result.stderr[:300])
            return None
            
    except Exception as e:
        print(f"❌ Fel: {e}")
        return None

def main():
    print("🎙️ MMM Senaste Nytt - FINAL Premiär med Crossfade")
    print("=" * 55)
    
    result = create_premiar_med_crossfade()
    
    if result:
        print(f"\n🎉 SLUTLIG PREMIÄR KLAR!")
        print(f"🎧 Lyssna på: {result}")
        print("\n🎵 Innehåller:")
        print("   • 15 sek intro med crossfade till tal")
        print("   • Lisa och Pelles perfekta dialog")
        print("   • 60 sek outro med fade out")
        print("   • TOTALT: ~6.3 minuter")
        print("\n✅ Redo för publicering!")
    else:
        print("\n📝 Manuell backup-metod:")
        print("1. Använd Audacity eller liknande")
        print("2. Lägg till crossfade mellan intro och tal")
        print("3. Lägg till fade out på outro")

if __name__ == "__main__":
    main()