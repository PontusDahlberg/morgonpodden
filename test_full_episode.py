#!/usr/bin/env python3
"""
TEST: Kör en fullständig podcast-generering lokalt för att testa längd och kvalitet
"""

import os
import sys
import logging
import subprocess
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_full_episode.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_episode_generation():
    """Testa att generera ett komplett avsnitt"""
    
    print("🎙️ TESTAR FULLSTÄNDIG AVSNITTSGENERERING")
    print("="*50)
    
    # Kontrollera att alla dependencies finns
    print("\n📋 Kontrollerar konfiguration...")
    
    required_files = [
        'sources.json',
        'run_podcast.py',
        'google-cloud-service-account.json',
        '.env'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Saknade filer: {missing_files}")
        return False
    
    print("✅ Alla nödvändiga filer finns")
    
    # Kontrollera sources.json konfiguration
    import json
    with open('sources.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Räkna aktiva källor
    active_sources = [s for s in config['sources'] if s.get('enabled', True)]
    total_max_items = sum(s.get('maxItems', 5) for s in active_sources)
    
    print(f"📰 Aktiva källor: {len(active_sources)}")
    print(f"📊 Max artiklar totalt: {total_max_items}")
    print(f"🎯 Målängd: {config['podcast_info']['duration_target']} minuter")
    
    # Starta podcast-generering
    print(f"\n🚀 Startar podcast-generering ({datetime.now().strftime('%H:%M:%S')})...")
    
    try:
        # Kör run_podcast.py utan auto-deploy för att testa lokalt
        result = subprocess.run([
            sys.executable, 'run_podcast.py', 
            '--test-mode',  # Om det finns en test mode
            '--verbose'
        ], capture_output=True, text=True, timeout=1800)  # 30 min timeout
        
        if result.returncode == 0:
            print("✅ Podcast-generering slutförd!")
            print("\nOutput:")
            print(result.stdout)
            
            # Analysera resultat
            analyze_results()
            
        else:
            print("❌ Podcast-generering misslyckades!")
            print("Error:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Timeout - genereringen tog för lång tid")
        return False
    except Exception as e:
        print(f"❌ Fel under generering: {e}")
        return False
    
    return True

def analyze_results():
    """Analysera genererade filer"""
    
    print("\n📊 ANALYSERAR RESULTAT")
    print("="*30)
    
    # Leta efter genererade audiofiler
    audio_dir = "audio/"
    if os.path.exists(audio_dir):
        audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.mp3')]
        latest_files = sorted([f for f in audio_files if 'intro_complete' in f])
        
        if latest_files:
            latest_file = latest_files[-1]
            file_path = os.path.join(audio_dir, latest_file)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            
            print(f"🎵 Senaste fil: {latest_file}")
            print(f"📁 Filstorlek: {file_size:.2f} MB")
            
            # Uppskatta längd baserat på filstorlek (cirka 1MB per minut för MP3)
            estimated_duration = file_size * 1.0  # Rough estimate
            print(f"⏱️ Uppskattad längd: {estimated_duration:.1f} minuter")
            
            if estimated_duration < 8:
                print("⚠️ VARNING: Avsnittet verkar vara för kort!")
                print("💡 Förslag: Öka maxItems i sources.json eller förbättra prompten")
            elif estimated_duration > 12:
                print("⚠️ VARNING: Avsnittet verkar vara för långt!")
            else:
                print("✅ Längden verkar vara bra!")
        else:
            print("❌ Inga färdiga audiofiler hittades")
    
    # Kolla generationslogg
    log_files = ['generation_log.txt', 'podcast_generation.log', 'test_full_episode.log']
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"\n📄 Logg: {log_file}")
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Visa sista 10 raderna
                for line in lines[-10:]:
                    print(f"   {line.strip()}")

def main():
    """Huvudfunktion"""
    
    print("🧪 MMM Senaste Nytt - Test av fullständig avsnittsgenerering")
    print(f"Starttid: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Kontrollera att vi är i rätt mapp
    if not os.path.exists('sources.json'):
        print("❌ Fel: Kör scriptet från morgonradio-mappen")
        sys.exit(1)
    
    # Kontrollera att vi har credentials
    if not os.path.exists('.env') or not os.path.exists('google-cloud-service-account.json'):
        print("❌ Fel: Saknade credentials-filer")
        print("Kontrollera att .env och google-cloud-service-account.json finns")
        sys.exit(1)
    
    success = test_episode_generation()
    
    if success:
        print("\n🎉 TEST SLUTFÖRT FRAMGÅNGSRIKT!")
        print("📁 Kolla audio/ mappen för genererade filer")
        print("📄 Kolla test_full_episode.log för detaljer")
    else:
        print("\n❌ TEST MISSLYCKADES")
        print("📄 Kolla test_full_episode.log för felmeddelanden")
    
    print(f"\nSluttid: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()