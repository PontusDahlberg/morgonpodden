#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BACKUP FAKTAKONTROLL: Pattern-based verification
Fungerar utan AI-API för grundläggande säkerhetskontroll
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class BasicFactChecker:
    """
    Enkel faktakontroll baserad på kända problemområden
    Fungerar utan AI-API som backup-säkerhet
    """
    
    def __init__(self):
        # Kända problematiska företag/personer (uppdatera regelbundet!)
        self.known_issues = {
            'bankrupt_companies': [
                'northvolt',  # Gick i konkurs 2024
            ],
            'outdated_positions': [
                'johan pehrson.*arbetsmarknadsminister',  # Inte längre minister
                'tobias billström.*utrikesminister',  # Inte längre utrikesminister
                'sveriges utrikesminister.*tobias billström',  # Explicit fel roll
            ],
            'suspicious_patterns': [
                r'investering.*6.*miljarder.*northvolt',  # Northvolt-investeringar
                r'johan pehrson.*säger.*igår',  # Utdaterade uttalanden
            ]
        }
    
    def basic_fact_check(self, text: str) -> Dict:
        """Grundläggande faktakontroll baserad på kända problem"""
        critical_issues = []  # Blockerar publicering
        warnings = []         # Varningar som inte blockerar
        
        text_lower = text.lower()
        
        # Kontrollera konkursade företag (KRITISKT)
        for company in self.known_issues['bankrupt_companies']:
            if company in text_lower:
                # Kontrollera om det är positivt omtal
                company_context = self._get_company_context(text, company)
                if self._is_positive_mention(company_context):
                    critical_issues.append(f"KRITISKT: {company.title()} nämns positivt men gick i konkurs 2024")
        
        # Kontrollera utdaterade positioner (KRITISKT)
        for position_pattern in self.known_issues['outdated_positions']:
            if re.search(position_pattern, text_lower):
                if 'billström' in position_pattern:
                    critical_issues.append(
                        "KRITISKT: Utdaterad ministerpost: Tobias Billström är inte Sveriges utrikesminister (numera Maria Malmer Stenergard)"
                    )
                else:
                    critical_issues.append(
                        "KRITISKT: Utdaterad ministerpost mentioned - Johan Pehrson är inte längre arbetsmarknadsminister"
                    )
        
        # Kontrollera misstänkta mönster (KRITISKT)
        for pattern in self.known_issues['suspicious_patterns']:
            if re.search(pattern, text_lower):
                critical_issues.append(f"KRITISKT: Misstänkt utdaterad information: {pattern}")
        
        # Allmänna varningssignaler (VARNINGAR - blockerar inte)
        general_warnings = self._check_general_warnings(text)
        warnings.extend(general_warnings)
        
        # Kombinera alla problem för rapportering
        all_issues = critical_issues + warnings
        
        return {
            'safe_to_publish': len(critical_issues) == 0,  # Endast kritiska fel blockerar
            'critical_issues': critical_issues,
            'warnings': warnings,
            'issues_found': all_issues,  # För bakåtkompatibilitet
            'check_type': 'basic_pattern_matching',
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_company_context(self, text: str, company: str, window: int = 200) -> str:
        """Hämta kontext runt företagsnamn"""
        company_lower = company.lower()
        text_lower = text.lower()
        
        pos = text_lower.find(company_lower)
        if pos == -1:
            return ""
        
        start = max(0, pos - window)
        end = min(len(text), pos + len(company) + window)
        
        return text[start:end]
    
    def _is_positive_mention(self, context: str) -> bool:
        """Kontrollera om företaget nämns i positiv kontext"""
        positive_words = [
            'investering', 'satsning', 'expansion', 'tillväxt', 'framgång',
            'miljarder', 'förebild', 'ledande', 'innovation', 'lanserar'
        ]
        
        context_lower = context.lower()
        return any(word in context_lower for word in positive_words)
    
    def _check_general_warnings(self, text: str) -> List[str]:
        """Kontrollera allmänna varningssignaler"""
        warnings = []
        
        # Kontrollera datum-referenser som kan vara utdaterade
        current_year = datetime.now().year
        if f"{current_year-1}" in text:  # Förra året
            warnings.append(f"KONTROLLERA: Referenser till {current_year-1} - kan vara utdaterat")
        
        # Kontrollera för "igår", "nyligen" etc som kan vara utdaterat
        time_sensitive = ['igår', 'i går', 'nyligen', 'denna vecka', 'förra veckan']
        for phrase in time_sensitive:
            if phrase in text.lower():
                warnings.append(f"KONTROLLERA: Tidskänslig referens '{phrase}' - verifiera aktualitet")
        
        # Kontrollera stora investeringsbelopp som ofta är utdaterade
        # Men undvik miljömått som "miljarder ton koldioxid"
        investment_pattern = r'(\d+)\s*(miljarder?|milliarder?)(?!\s*(ton|kilo|gram))'
        matches = re.finditer(investment_pattern, text.lower())
        for match in matches:
            context = text[max(0, match.start()-50):match.end()+50].lower()
            amount = match.group(1)
            
            # Skippa om det handlar om miljömått eller vetenskapliga värden
            if any(word in context for word in ['koldioxid', 'ton', 'utsläpp', 'energi', 'watt', 'klimat']):
                continue
                
            if int(amount) > 1:  # Stora belopp
                warnings.append(f"KONTROLLERA: Stor investering ({amount} miljarder) - verifiera källa och datum")
        
        return warnings

def quick_fact_check(script_text: str) -> bool:
    """Snabb faktakontroll som returnerar True om säkert att publicera"""
    checker = BasicFactChecker()
    result = checker.basic_fact_check(script_text)
    
    if not result['safe_to_publish']:
        print("\n🚨 FAKTAKONTROLL VARNING:")
        for issue in result['issues_found']:
            print(f"- {issue}")
        print("\nRekommendation: Granska och korrigera innan publicering!")
    
    return result['safe_to_publish']

if __name__ == "__main__":
    # Test med känd problematisk text
    test_text = """
    Lisa: Northvolt har just fått en stor investering på 6 miljarder kronor.
    Pelle: Ja, och arbetsmarknadsminister Johan Pehrson sa i går att detta kommer skapa tusentals jobb.
    """
    
    print("Testar grundläggande faktakontroll...")
    is_safe = quick_fact_check(test_text)
    print(f"Säkert att publicera: {is_safe}")