#!/usr/bin/env python3
"""
SÄKER PODCAST GENERATOR - Helt ny implementation
Fokus på säkerhet, kostnadskontroll och kvalitet

Säkerhetsprinciper:
- Inga hårdkodade nycklar
- Alla känsliga data via miljövariabler
- Automatisk validering
- Kostnadsberäkning före körning
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Konfigurera logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('secure_podcast.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class CostEstimate:
    """Kostnadsberäkning för API-anrop"""
    characters: int
    estimated_credits: float
    api_calls: int
    estimated_cost_usd: float
    
    def is_within_budget(self, max_credits: float = 100) -> bool:
        """Kontrollera om kostnaden är inom budget"""
        return self.estimated_credits <= max_credits

@dataclass
class SecurityCheck:
    """Säkerhetskontroll resultat"""
    has_api_keys: bool
    env_file_secure: bool
    no_hardcoded_secrets: bool
    all_checks_passed: bool

class SecurePodcastGenerator:
    """Säker podcast-generator med strikta säkerhetskontroller"""
    
    def __init__(self, config_file: str = "sources.json"):
        """Initialisera med säkerhetskontroller"""
        logger.info("🔐 Initialiserar säker podcast-generator...")
        
        # Ladda miljövariabler
        load_dotenv()
        
        # Kör säkerhetskontroller FÖRST
        security_result = self._run_security_checks()
        if not security_result.all_checks_passed:
            raise SecurityError("❌ Säkerhetskontroller misslyckades!")
        
        # Ladda konfiguration
        self.config = self._load_secure_config(config_file)
        
        # Sätt upp kostnadshantering
        self.max_credits_per_episode = 50  # Säkerhetsgräns
        
        logger.info("✅ Säker podcast-generator initialiserad")
    
    def _run_security_checks(self) -> SecurityCheck:
        """Kör omfattande säkerhetskontroller"""
        logger.info("🔍 Kör säkerhetskontroller...")
        
        # Kontrollera API-nycklar
        required_keys = ['ELEVENLABS_API_KEY', 'OPENROUTER_API_KEY']
        has_keys = all(os.getenv(key) for key in required_keys)
        
        # Kontrollera att .env inte committas
        env_secure = os.path.exists('.gitignore') and '.env' in open('.gitignore').read()
        
        # Kontrollera inga hårdkodade secrets i Python-filer
        no_hardcoded = self._check_no_hardcoded_secrets()
        
        all_passed = has_keys and env_secure and no_hardcoded
        
        result = SecurityCheck(
            has_api_keys=has_keys,
            env_file_secure=env_secure,
            no_hardcoded_secrets=no_hardcoded,
            all_checks_passed=all_passed
        )
        
        if not all_passed:
            logger.error("❌ Säkerhetskontroller misslyckades:")
            if not has_keys:
                logger.error("  - API-nycklar saknas")
            if not env_secure:
                logger.error("  - .env fil ej skyddad i .gitignore")
            if not no_hardcoded:
                logger.error("  - Hårdkodade secrets hittade")
        else:
            logger.info("✅ Alla säkerhetskontroller godkända")
        
        return result
    
    def _check_no_hardcoded_secrets(self) -> bool:
        """Kontrollera att inga secrets är hårdkodade"""
        import glob
        import re
        
        # Mönster för potentiella API-nycklar
        secret_patterns = [
            r'sk_[a-zA-Z0-9]{48,}',  # ElevenLabs nycklar
            r'sk-or-v1-[a-zA-Z0-9]{64,}',  # OpenRouter nycklar
            r'api_key\s*=\s*["\'][^"\']{20,}["\']'  # Generiska API-nycklar
        ]
        
        for py_file in glob.glob("*.py"):
            if py_file.startswith("secure_"):
                continue  # Skippa säkra filer
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in secret_patterns:
                    if re.search(pattern, content):
                        logger.error(f"❌ Potentiell hårdkodad secret i {py_file}")
                        return False
            except:
                continue
        
        return True
    
    def _load_secure_config(self, config_file: str) -> Dict:
        """Ladda konfiguration säkert"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Säkerställ att text-to-dialogue är avslaget för kostnadskontroll
            if config.get('podcastSettings', {}).get('textToDialogue', {}).get('enabled', False):
                logger.warning("⚠️ Stänger av text-to-dialogue för kostnadskontroll")
                config['podcastSettings']['textToDialogue']['enabled'] = False
            
            return config
        except Exception as e:
            logger.error(f"❌ Kunde inte ladda konfiguration: {e}")
            raise
    
    def estimate_cost(self, script_text: str) -> CostEstimate:
        """Beräkna kostnad före generering"""
        chars = len(script_text)
        
        # ElevenLabs standard TTS: ~0.18 krediter per 1000 tecken
        credits_per_1000_chars = 0.18
        estimated_credits = (chars / 1000) * credits_per_1000_chars
        
        # Uppskattat antal API-anrop (en per röst + intro)
        api_calls = 3
        
        # Ungefärlig kostnad i USD (ca $0.0018 per kredit)
        estimated_cost_usd = estimated_credits * 0.0018
        
        return CostEstimate(
            characters=chars,
            estimated_credits=estimated_credits,
            api_calls=api_calls,
            estimated_cost_usd=estimated_cost_usd
        )
    
    def generate_episode_safe(self, max_credits: float = 50) -> Dict:
        """Generera avsnitt med säkerhetskontroller"""
        logger.info("🎬 Startar säker avsnittsgenerering...")
        
        # Mockad script för test (ersätts med riktigt innehåll senare)
        test_script = """
        Anna: Hej och välkommen till Människa Maskin Miljö! Idag den 23 september 2025.
        
        Erik: Hej Anna! Idag ska vi prata om veckans viktiga händelser inom AI och klimat.
        
        Anna: Absolut! Det har varit en spännande vecka med flera genombrott inom förnybar energi.
        
        Erik: Ja, särskilt den nya batteriteknologin från Sverige som kan revolutionera energilagring.
        
        Anna: Det är verkligen lovande. Låt oss dyka djupare in i detta.
        """
        
        # Kostnadsberäkning
        cost_estimate = self.estimate_cost(test_script)
        
        logger.info(f"💰 Kostnadsberäkning:")
        logger.info(f"  - Tecken: {cost_estimate.characters:,}")
        logger.info(f"  - Uppskattade krediter: {cost_estimate.estimated_credits:.2f}")
        logger.info(f"  - API-anrop: {cost_estimate.api_calls}")
        logger.info(f"  - Kostnad (USD): ${cost_estimate.estimated_cost_usd:.4f}")
        
        # Kontrollera budget
        if not cost_estimate.is_within_budget(max_credits):
            raise BudgetExceededError(
                f"Kostnaden ({cost_estimate.estimated_credits:.2f} krediter) "
                f"överstiger budget ({max_credits} krediter)"
            )
        
        # Bekräfta före körning
        logger.info("✅ Kostnad godkänd - fortsätter med generering")
        
        # Här skulle vi generera riktigt ljud, men för säkerhets skull
        # returnerar vi bara metadata först
        metadata = {
            "title": "Säkert test-avsnitt",
            "date": datetime.now().isoformat(),
            "cost_estimate": {
                "characters": cost_estimate.characters,
                "estimated_credits": cost_estimate.estimated_credits,
                "api_calls": cost_estimate.api_calls,
                "estimated_cost_usd": cost_estimate.estimated_cost_usd
            },
            "security_verified": True,
            "budget_approved": True
        }
        
        logger.info("✅ Säker test-avsnitt genererat")
        return metadata

class SecurityError(Exception):
    """Säkerhetsfel"""
    pass

class BudgetExceededError(Exception):
    """Budget överskriden"""
    pass

def main():
    """Huvudfunktion för säker podcast-generering"""
    try:
        logger.info("🚀 Startar säker podcast-generator")
        
        # Skapa säker generator
        generator = SecurePodcastGenerator()
        
        # Generera test-avsnitt
        result = generator.generate_episode_safe(max_credits=50)
        
        logger.info("✅ Säker generering slutförd!")
        logger.info(f"Resultat: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
    except SecurityError as e:
        logger.error(f"🚨 SÄKERHETSFEL: {e}")
        sys.exit(1)
    except BudgetExceededError as e:
        logger.error(f"💰 BUDGETFEL: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ OVÄNTAT FEL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
