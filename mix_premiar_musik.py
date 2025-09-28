#!/usr/bin/env python3
"""
Enkel musikmixer för att lägga till intro/bryggor/outro till premiäravsnittet
"""

import subprocess
import os
import shutil

def add_music_to_episode(voice_file, output_file="audio/premiar_med_musik.mp3"):
    """Lägger till musik till premiäravsnittet"""
    
    if not os.path.exists(voice_file):
        print(f"❌ Kan inte hitta röstsfilmen: {voice_file}")
        return None
        
    # Kontrollera om ffmpeg finns
    if not shutil.which('ffmpeg'):
        print("⚠️ ffmpeg inte installerat - kan inte mixa musik automatiskt")
        print("📝 Manuell instruktion:")
        print(f"   1. Lägg till 20 sek intro från: audio/music/088d314d.mp3")
        print(f"   2. Redigera in 3x 8-sek bryggor från: audio/music/e5693973.mp3")
        print(f"   3. Lägg till 25 sek outro från: audio/music/9858802e.mp3")
        print(f"   4. Röstfil att använda: {voice_file}")
        return voice_file
    
    try:
        print("🎵 Skapar premiäravsnitt med musik...")
        
        # Enklare approach: Lägg bara till intro och outro runt rösterna
        cmd = [
            'ffmpeg', '-y',  # Överskriv output
            
            # Input filer
            '-i', 'audio/music/088d314d.mp3',  # [0] Intro musik  
            '-i', voice_file,                   # [1] Röstfil
            '-i', 'audio/music/9858802e.mp3',  # [2] Outro musik
            
            # Filter: Klipp och sätt ihop
            '-filter_complex', 
            '[0:a]atrim=0:20,volume=0.6[intro];'     # 20 sek intro, lägre volym
            '[1:a]volume=1.0[voice];'                 # Röst normal volym  
            '[2:a]atrim=0:25,volume=0.4[outro];'     # 25 sek outro, låg volym
            '[intro][voice][outro]concat=n=3:v=0:a=1,aresample=44100[out]',  # Sätt ihop
            
            '-map', '[out]',
            '-c:a', 'mp3',   # MP3 codec
            '-b:a', '192k',  # 192kbps bitrate
            output_file
        ]
        
        print("🔧 Kör förbättrad ffmpeg mixning...")
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            print(f"✅ Premiär med musik skapad: {output_file}")
            
            # Kontrollera filstorlek för att se att något skapades
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                if file_size > 100000:  # Större än 100KB
                    print(f"📊 Filstorlek: {file_size/1024/1024:.1f} MB - ser bra ut!")
                else:
                    print(f"⚠️ Filstorlek: {file_size} bytes - något kan vara fel")
            
            return output_file
        else:
            print(f"❌ ffmpeg fel (returnkod {result.returncode}):")
            print(f"Stderr: {result.stderr[:500]}")  # Första 500 tecken
            return None
            
    except Exception as e:
        print(f"❌ Fel vid musikmixning: {e}")
        return None

def main():
    """Huvudfunktion för att mixa musik till premiären"""
    
    voice_file = "audio/episode_google_service_account.mp3"
    
    print("🎙️ MMM Senaste Nytt - Premiär med musik")
    print("=" * 45)
    
    if not os.path.exists(voice_file):
        print(f"❌ Kan inte hitta röstsfilmen: {voice_file}")
        print("💡 Kör först: python test_premiar_uppdaterat.py")
        return
    
    result = add_music_to_episode(voice_file)
    
    if result:
        print(f"\n🎉 PREMIÄREN ÄR KLAR!")
        print(f"🎧 Lyssna på: {result}")
        print("\n🎵 Innehåller:")
        print("   • 20 sek intro (088d314d.mp3)")
        print("   • Lisa och Pelles reviderade dialog")
        print("   • 25 sek outro (9858802e.mp3)")
        print("\n💡 Bryggor behöver läggas till manuellt mellan segment")
    else:
        print(f"\n📝 Använd den befintliga filen: {voice_file}")
        print("🎵 Lägg till musik manuellt enligt instruktionerna ovan")

if __name__ == "__main__":
    main()