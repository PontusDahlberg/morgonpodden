#!/usr/bin/env python3
"""
Enkel backup-metod för att skapa premiär med musik - steg för steg
"""

import os

def create_simple_premiar():
    """Skapar premiär genom att visa steg-för-steg instruktioner"""
    
    voice_file = "audio/episode_google_service_account.mp3"
    
    if not os.path.exists(voice_file):
        print("❌ Röstfilen saknas - kör först: python test_premiar_uppdaterat.py")
        return
    
    print("🎙️ ENKEL PREMIÄR-MIXNING - Steg för steg")
    print("=" * 50)
    print()
    print("📁 FILER DU BEHÖVER:")
    print(f"   🎤 Röst: {voice_file}")
    print("   🎵 Intro: audio/music/088d314d.mp3 (första 20 sekunder)")
    print("   🎵 Outro: audio/music/9858802e.mp3 (första 25 sekunder)")
    print()
    print("🔧 MANUELL METOD (rekommenderas):")
    print("1. Öppna din audioeditor (Audacity, Adobe Audition, etc)")
    print("2. Importera alla tre filer")
    print("3. Klipp 088d314d.mp3 till 20 sekunder")
    print("4. Klipp 9858802e.mp3 till 25 sekunder")
    print("5. Lägg i ordning: Intro -> Röst -> Outro")
    print("6. Justera volymerna:")
    print("   • Intro musik: 60% volym")
    print("   • Röst: 100% volym")
    print("   • Outro musik: 40% volym")
    print("7. Exportera som MP3")
    print()
    print("⏱️ RESULTAT:")
    print("   • ~20 sek intro")
    print("   • ~3.4 min dialog (Lisa & Pelle)")  
    print("   • ~25 sek outro")
    print("   • TOTALT: ~6 minuter")
    print()
    print("🎧 Testa först den nuvarande filen: audio/premiar_med_musik.mp3")
    print("Om den bara innehåller musik, använd manuell metod ovan.")

if __name__ == "__main__":
    create_simple_premiar()