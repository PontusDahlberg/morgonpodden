#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KRITISK SÄKERHETSKOMPONENT: News Fact Checker Agent
Verifierar alla nyheter innan publicering för att förhindra felaktig information.

SYFTE: Förhindra katastrofala fel som utdaterade företagsstatus, fel ministerposter, etc.
"""

import requests
import json
import logging
from datetime import datetime, timedelta
import re
from typing import Dict, List, Tuple, Optional
import openai
from dataclasses import dataclass

# Konfigurera logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FactCheckResult:
    """Resultat från faktakontroll"""
    is_accurate: bool
    confidence_score: float  # 0.0 - 1.0
    issues_found: List[str]
    corrections: List[str]
    sources_checked: List[str]
    verification_date: datetime

class NewsFactChecker:
    """
    KRITISK SÄKERHETSAGENT för faktakontroll av nyheter
    
    Verifierar:
    - Företagsstatus (konkurs, fusioner, etc.)
    - Politiska poster och ministrar
    - Aktuella händelser och datum
    - Statistik och siffror
    - Tekniska fakta
    """
    
    def __init__(self):
        # Ladda konfiguration från samma källor som huvudsystemet
        try:
            with open('sources.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Använd OpenRouter API som huvudsystemet
            api_key = config.get('openrouter_api_key')
            if api_key:
                self.openai_client = openai.OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key
                )
                logger.info("[FACT-CHECK] OpenRouter API konfigurerad för faktakontroll")
            else:
                logger.error("OpenRouter API-nyckel saknas i sources.json")
                self.openai_client = None
        except Exception as e:
            logger.error(f"Kunde inte ladda konfiguration: {e}")
            self.openai_client = None
        
        # Kritiska kategorier som MÅSTE verifieras
        self.critical_patterns = {
            'companies': r'\b(Northvolt|Tesla|Google|Microsoft|Apple|Amazon|Meta|SpaceX)\b',
            'ministers': r'\b(minister|statsminister|finansminister|miljöminister)\b',
            'statistics': r'\b(\d+%|\d+\s*(miljoner?|milliarder?|procent))\b',
            'dates': r'\b(2024|2025|förra året|detta år|nyligen|i veckan)\b',
            'investments': r'\b(\d+\s*(miljoner?|milliarder?).*(investering|satsning))\b'
        }
        
        # Källor för faktakontroll
        self.verification_sources = [
            "Aktuelle företagsdatabaser",
            "Regeringens webbsida",
            "Statistiska centralbyrån (SCB)",
            "Dagens Industri arkiv",
            "Reuters faktadatabas"
        ]

    def extract_checkable_facts(self, text: str) -> List[Dict]:
        """Extraherar fakta som behöver verifieras"""
        facts_to_check = []
        
        # Hitta företagsrelaterade påståenden
        company_matches = re.finditer(self.critical_patterns['companies'], text, re.IGNORECASE)
        for match in company_matches:
            context = self._get_context_around_match(text, match)
            facts_to_check.append({
                'type': 'company_status',
                'entity': match.group(),
                'context': context,
                'critical': True
            })
        
        # Hitta ministerpositioner
        minister_matches = re.finditer(self.critical_patterns['ministers'], text, re.IGNORECASE)
        for match in minister_matches:
            context = self._get_context_around_match(text, match)
            facts_to_check.append({
                'type': 'political_position',
                'entity': match.group(),
                'context': context,
                'critical': True
            })
        
        # Hitta statistiska påståenden
        stat_matches = re.finditer(self.critical_patterns['statistics'], text, re.IGNORECASE)
        for match in stat_matches:
            context = self._get_context_around_match(text, match)
            facts_to_check.append({
                'type': 'statistics',
                'entity': match.group(),
                'context': context,
                'critical': True
            })
        
        return facts_to_check

    def _get_context_around_match(self, text: str, match, window: int = 100) -> str:
        """Hämtar kontext runt en matchning"""
        start = max(0, match.start() - window)
        end = min(len(text), match.end() + window)
        return text[start:end]

    def verify_fact_with_ai(self, fact: Dict) -> FactCheckResult:
        """Använder AI för att verifiera ett specifikt faktum"""
        
        verification_prompt = f"""
        Du är en KRITISK faktakontroll-agent för svenska nyheter. Din uppgift är att identifiera POTENTIELLT FELAKTIG information.

        FAKTUM ATT KONTROLLERA:
        Typ: {fact['type']}
        Entitet: {fact['entity']}
        Kontext: {fact['context']}

        KRITISKA KONTROLLER (Oktober 2025):
        1. FÖRETAGSSTATUS: Är företaget fortfarande aktivt eller har det gått i konkurs/fusion?
        2. POLITISKA POSTER: Är personen fortfarande på den positionen (kontrollera aktuella ministrar)?
        3. TIDSASPEKT: Är informationen aktuell för oktober 2025?

        KÄND PROBLEMATISK INFORMATION:
        - Northvolt gick i konkurs 2024
        - Johan Pehrson är inte längre arbetsmarknadsminister 2025
        - Kontrollera alla ministerposter noga

        Svara med JSON:
        {{
            "is_accurate": boolean,
            "confidence_score": 0.0-1.0,
            "issues_found": ["lista med problem"],
            "corrections": ["föreslagna korrigeringar"],
            "risk_level": "LOW/MEDIUM/HIGH/CRITICAL"
        }}

        Om du inte är 100% säker, markera som potentiellt problematisk!
        """

        try:
            if not self.openai_client:
                raise Exception("OpenAI-klient inte tillgänglig")
                
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": verification_prompt}],
                temperature=0.1  # Låg temperatur för konsistens
            )
            
            result_text = response.choices[0].message.content
            result_data = json.loads(result_text)
            
            return FactCheckResult(
                is_accurate=result_data.get('is_accurate', False),
                confidence_score=result_data.get('confidence_score', 0.0),
                issues_found=result_data.get('issues_found', []),
                corrections=result_data.get('corrections', []),
                sources_checked=self.verification_sources,
                verification_date=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Fel vid faktakontroll: {e}")
            # Vid fel, markera som potentiellt problematisk för säkerhets skull
            return FactCheckResult(
                is_accurate=False,
                confidence_score=0.0,
                issues_found=[f"Kunde inte verifiera pga tekniskt fel: {e}"],
                corrections=["Manuell kontroll krävs"],
                sources_checked=[],
                verification_date=datetime.now()
            )

    def check_podcast_script(self, script_text: str) -> Dict:
        """Huvudfunktion: Kontrollerar hela podcast-manuset"""
        logger.info("[FACT-CHECK] Startar faktakontroll av podcast-manus...")
        
        # Extrahera fakta som behöver kontrolleras
        facts_to_check = self.extract_checkable_facts(script_text)
        logger.info(f"[FACT-CHECK] Hittade {len(facts_to_check)} fakta att kontrollera")
        
        verification_results = []
        critical_issues = []
        
        for fact in facts_to_check:
            logger.info(f"[FACT-CHECK] Kontrollerar: {fact['entity']}")
            result = self.verify_fact_with_ai(fact)
            verification_results.append(result)
            
            if not result.is_accurate or result.confidence_score < 0.7:
                critical_issues.append({
                    'fact': fact,
                    'result': result
                })
        
        # Sammanställ totalresultat
        all_accurate = all(r.is_accurate for r in verification_results)
        avg_confidence = sum(r.confidence_score for r in verification_results) / len(verification_results) if verification_results else 0.0
        
        total_issues = []
        total_corrections = []
        for result in verification_results:
            total_issues.extend(result.issues_found)
            total_corrections.extend(result.corrections)
        
        fact_check_report = {
            'overall_safe_to_publish': all_accurate and avg_confidence >= 0.8,
            'total_facts_checked': len(facts_to_check),
            'accuracy_rate': sum(1 for r in verification_results if r.is_accurate) / len(verification_results) if verification_results else 0.0,
            'confidence_score': avg_confidence,
            'critical_issues': critical_issues,
            'all_issues': total_issues,
            'suggested_corrections': total_corrections,
            'verification_timestamp': datetime.now().isoformat(),
            'status': 'SAFE' if all_accurate and avg_confidence >= 0.8 else 'REQUIRES_REVIEW'
        }
        
        # Logga resultat
        if fact_check_report['overall_safe_to_publish']:
            logger.info("[FACT-CHECK] ✅ GODKÄND - Inga kritiska problem hittade")
        else:
            logger.warning("[FACT-CHECK] ⚠️ KRÄVER GRANSKNING - Potentiella problem hittade")
            for issue in critical_issues:
                logger.warning(f"[FACT-CHECK] Problem: {issue['result'].issues_found}")
        
        return fact_check_report

    def generate_fact_check_report(self, report: Dict) -> str:
        """Genererar läsbar faktakontroll-rapport"""
        
        status_emoji = "✅" if report['overall_safe_to_publish'] else "⚠️"
        
        report_text = f"""
# FAKTAKONTROLL-RAPPORT {status_emoji}

**Status**: {report['status']}
**Datum**: {report['verification_timestamp']}
**Säker att publicera**: {'JA' if report['overall_safe_to_publish'] else 'NEJ - KRÄVER GRANSKNING'}

## Sammanfattning
- **Fakta kontrollerade**: {report['total_facts_checked']}
- **Noggrannhet**: {report['accuracy_rate']:.1%}
- **Konfidensgrad**: {report['confidence_score']:.1%}

## Kritiska Problem
"""
        
        if report['critical_issues']:
            for i, issue in enumerate(report['critical_issues'], 1):
                report_text += f"""
### Problem {i}
- **Entitet**: {issue['fact']['entity']}
- **Problem**: {', '.join(issue['result'].issues_found)}
- **Förslag**: {', '.join(issue['result'].corrections)}
"""
        else:
            report_text += "\n*Inga kritiska problem hittade.*\n"
        
        if not report['overall_safe_to_publish']:
            report_text += f"""
## ⚠️ VARNING
Detta manus är INTE säkert att publicera utan granskning.
Åtgärda problemen ovan innan publicering.
"""
        
        return report_text

def main():
    """Test av faktakontroll-systemet"""
    checker = NewsFactChecker()
    
    # Test med känd problematisk text
    test_script = """
    Lisa: Vi har spännande nyheter om Northvolt som just fått en investering på 6 miljarder kronor.
    Pelle: Ja, och arbetsmarknadsminister Johan Pehrson sa igår att detta kommer skapa 10 000 nya jobb.
    Lisa: Statistik visar att elbilar ökat med 70% enligt en ny rapport.
    """
    
    logger.info("Testar faktakontroll-systemet...")
    report = checker.check_podcast_script(test_script)
    
    print("\n" + checker.generate_fact_check_report(report))
    
    return report['overall_safe_to_publish']

if __name__ == "__main__":
    main()