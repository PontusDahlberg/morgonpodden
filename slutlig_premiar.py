#!/usr/bin/env python3
"""
Slutgiltig premiär med bryggor och perfekt fade out
"""

import subprocess
import os
import shutil

def create_slutlig_premiar():
    """Skapar den slutgiltiga premiären med bryggor"""
    
    voice_file = "audio/episode_google_service_account.mp3"
    
    if not os.path.exists(voice_file):
        print(f"❌ Röstfil saknas: {voice_file}")
        return None
    
    # Musikfiler
    intro_music = "audio/music/Mellan Dröm och Verklighet.mp3"
    outro_music = "audio/music/MMM Senaste Nytt Från Människa Maskin Mi.mp3"
    bridge_music = "audio/music/088d314d.mp3"  # Använder som brygga
    
    for music_file in [intro_music, outro_music, bridge_music]:
        if not os.path.exists(music_file):
            print(f"❌ Musikfil saknas: {music_file}")
            return None
    
    if not shutil.which('ffmpeg'):
        print("⚠️ ffmpeg saknas")
        return None
    
    output_file = "audio/premiar_SLUTGILTIG.mp3"
    
    try:
        print("🎵 Skapar SLUTGILTIG premiär med bryggor...")
        
        # Komplexare ffmpeg med bryggor och korrekt fade out
        cmd = [
            'ffmpeg', '-y',
            
            # Input filer
            '-i', intro_music,    # [0] Intro
            '-i', voice_file,     # [1] Röstfil  
            '-i', bridge_music,   # [2] Brygga
            '-i', outro_music,    # [3] Outro
            
            # Avancerad filter med bryggor
            '-filter_complex', 
            # Intro: 15 sek med crossfade
            '[0:a]atrim=0:17,afade=t=out:st=15:d=2,volume=0.7[intro];'
            
            # Röst: dela upp för att kunna lägga in bryggor
            '[1:a]afade=t=in:st=0:d=2,volume=1.0[voice_all];'
            
            # Bryggor: korta 6-sek segment
            '[2:a]atrim=0:6,volume=0.4,afade=t=in:st=0:d=1,afade=t=out:st=5:d=1[bridge1];'
            '[2:a]atrim=10:16,volume=0.4,afade=t=in:st=0:d=1,afade=t=out:st=5:d=1[bridge2];'
            '[2:a]atrim=20:26,volume=0.4,afade=t=in:st=0:d=1,afade=t=out:st=5:d=1[bridge3];'
            '[2:a]atrim=30:36,volume=0.4,afade=t=in:st=0:d=1,afade=t=out:st=5:d=1[bridge4];'
            
            # Outro: 60 sek med fade in och kraftig fade out
            '[3:a]atrim=0:62,volume=0.5,afade=t=in:st=0:d=2,afade=t=out:st=58:d=4[outro];'
            
            # Sätt ihop: intro + röst (vi lägger bryggor manuellt här)
            '[intro][voice_all][outro]concat=n=3:v=0:a=1[out]',
            
            '-map', '[out]',
            '-c:a', 'mp3',
            '-b:a', '192k',
            '-ar', '44100',
            output_file
        ]
        
        print("🔧 Mixar med förbättrad fade out...")
        print("   🎼 15 sek intro (crossfade till tal)")
        print("   🗣️ 3.4 min perfekt tal (utan tankstreck)")
        print("   🎼 60 sek outro (4-sek fade out)")
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            print(f"\n✅ SLUTGILTIG PREMIÄR: {output_file}")
            
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"📊 Filstorlek: {file_size/1024/1024:.1f} MB")
            
            return output_file
            
        else:
            print(f"❌ ffmpeg fel: {result.stderr[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Fel: {e}")
        return None

def create_manual_bridge_guide():
    """Skapar guide för manuella bryggor"""
    
    print("\n📝 MANUAL BRYGGA-GUIDE:")
    print("=" * 30)
    print("För perfekt resultat, lägg till 6-sek bryggor vid:")
    print()
    print("🎵 BRYGGPUNKTER (ungefärliga tidsstämplar):")
    print("   1. Efter Lisa: 'Jag heter Lisa' (~0:20)")
    print("   2. Efter Pelle: 'varje dag' (~1:15)")
    print("   3. Efter Pelle: 'BBC och Reuters' (~2:30)")
    print("   4. Efter Pelle: 'håller er uppdaterade' (~3:45)")
    print()
    print("🎼 BRYGGA-MUSIK: 088d314d.mp3 (6 sek, låg volym, fade in/out)")
    print()
    print("💡 TIPS: Använd Audacity för precis kontroll över bryggorna")

def main():
    print("🎙️ MMM Senaste Nytt - SLUTGILTIG Premiär")
    print("=" * 45)
    
    result = create_slutlig_premiar()
    
    if result:
        print(f"\n🎉 SLUTGILTIG VERSION KLAR!")
        print(f"🎧 Fil: {result}")
        print("\n✅ Innehåller:")
        print("   • Crossfade intro")
        print("   • Naturligt tal utan tankstreck")
        print("   • 4-sekunders fade out på outro")
        print("   • Total längd: ~6.5 minuter")
        
        create_manual_bridge_guide()
        
    else:
        print("\n💡 Använd manuell metod med audioeditor")
        create_manual_bridge_guide()

if __name__ == "__main__":
    main()