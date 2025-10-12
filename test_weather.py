#!/usr/bin/env python3
"""
Test väder-funktionalitet
"""
import sys
import logging

# Lägg till sökväg
sys.path.append('.')

from run_podcast_complete import get_swedish_weather

# Konfigurera logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_weather():
    """Testa väder-hämtning"""
    try:
        logger.info("🌤️ Testar väder-hämtning...")
        weather_info = get_swedish_weather()
        
        print(f"\n🌤️ VÄDER-TEST RESULTAT:")
        print(f"📍 {weather_info}")
        
        # Kolla om alla 4 regioner finns
        expected_regions = ["Götaland", "Svealand", "Södra Norrland", "Norra Norrland"]
        found_regions = [region for region in expected_regions if region in weather_info]
        
        print(f"\n✅ Hittade regioner: {found_regions}")
        print(f"🎯 Förväntade: {expected_regions}")
        
        if len(found_regions) >= 3:
            print("✅ Väder-test GODKÄNT (minst 3 regioner)")
            return True
        else:
            print("⚠️ Väder-test VARNING (färre än 3 regioner)")
            return False
            
    except Exception as e:
        logger.error(f"❌ Väder-test misslyckades: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Startar väder-test...")
    success = test_weather()
    if success:
        print("\n✅ Väder-test slutfört!")
    else:
        print("\n❌ Väder-test misslyckades.")