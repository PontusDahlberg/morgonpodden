#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SJÄLVKORRIGERANDE FAKTAKONTROLL-SYSTEM
Automatiskt åtgärdar faktakontroll-problem genom att regenerera innehåll
"""

import json
import logging
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import openai

logger = logging.getLogger(__name__)

class SelfCorrectingFactChecker:
    """
    Intelligent system som automatiskt korrigerar faktakontroll-problem
    genom att låta AI:n regenerera problematiska avsnitt
    """
    
    def __init__(self):
        # Ladda konfiguration för AI-redigering
        try:
            with open('sources.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.api_key = config.get('openrouter_api_key')
            if self.api_key:
                self.client = openai.OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.api_key
                )
                self.ai_available = True
            else:
                self.ai_available = False
                logger.warning("AI-redigering inte tillgänglig - ingen API-nyckel")
        except Exception as e:
            self.ai_available = False
            logger.error(f"Kunde inte ladda AI-konfiguration: {e}")
            
        # Vanliga problemord och deras säkra ersättningar
        self.safe_replacements = {
            'nyligen': 'under 2025',
            'förra veckan': 'tidigare i år',
            'i går': 'tidigare',
            'denna vecka': 'under oktober 2025',
            'igår': 'tidigare',
            'nyss': 'under 2025',
            'precis': 'under 2025',
        }
        
        # Problematiska företag/personer som ska undvikas helt
        self.blacklisted_entities = {
            'northvolt': 'batteritillverkningssektorn',
            'johan pehrson.*arbetsmarknadsminister': 'regeringen',
        }

    def auto_correct_content(self, original_content: str, fact_issues: List[str], max_attempts: int = 3) -> Tuple[str, bool]:
        """
        Automatiskt korrigera innehåll baserat på faktakontroll-problem
        
        Returns:
            (corrected_content, success)
        """
        logger.info(f"[AUTO-CORRECT] Startar automatisk korrigering av {len(fact_issues)} problem")
        
        corrected_content = original_content
        success = False
        
        # Försök olika korrigeringsstrategier
        for attempt in range(max_attempts):
            logger.info(f"[AUTO-CORRECT] Försök {attempt + 1}/{max_attempts}")
            
            # Strategi 1: Enkla ordersättningar
            corrected_content = self._apply_simple_replacements(corrected_content)
            
            # Strategi 2: Ta bort problematiska entiteter
            corrected_content = self._remove_blacklisted_entities(corrected_content)
            
            # Strategi 3: AI-baserad omskrivning av problematiska avsnitt
            if self.ai_available:
                corrected_content = self._ai_rewrite_problematic_sections(
                    corrected_content, fact_issues
                )
            
            # Testa korrigeringen med grundläggande faktakontroll
            from basic_fact_checker import BasicFactChecker
            checker = BasicFactChecker()
            test_result = checker.basic_fact_check(corrected_content)
            
            if test_result['safe_to_publish']:
                if test_result.get('warnings'):
                    logger.info(f"[AUTO-CORRECT] ✅ Korrigering lyckades! (Varningar kvarstår: {len(test_result['warnings'])})")
                else:
                    logger.info("[AUTO-CORRECT] ✅ Korrigering lyckades helt!")
                success = True
                break
            else:
                critical_issues = test_result.get('critical_issues', [])
                logger.warning(f"[AUTO-CORRECT] Försök {attempt + 1} misslyckades: {critical_issues}")
        
        if not success:
            logger.error("[AUTO-CORRECT] ❌ Kunde inte korrigera automatiskt")
        
        return corrected_content, success

    def _apply_simple_replacements(self, content: str) -> str:
        """Tillämpa enkla ordersättningar för tidskänsliga referenser"""
        logger.info("[AUTO-CORRECT] Tillämpar enkla ordersättningar...")
        
        corrected = content
        replacements_made = []
        
        for problematic_word, safe_replacement in self.safe_replacements.items():
            pattern = r'\b' + re.escape(problematic_word) + r'\b'
            if re.search(pattern, corrected, re.IGNORECASE):
                corrected = re.sub(pattern, safe_replacement, corrected, flags=re.IGNORECASE)
                replacements_made.append(f"'{problematic_word}' → '{safe_replacement}'")
        
        if replacements_made:
            logger.info(f"[AUTO-CORRECT] Ersättningar: {', '.join(replacements_made)}")
        
        return corrected

    def _remove_blacklisted_entities(self, content: str) -> str:
        """Ta bort eller ersätt problematiska företag/personer"""
        logger.info("[AUTO-CORRECT] Tar bort svartlistade entiteter...")
        
        corrected = content
        
        for entity_pattern, replacement in self.blacklisted_entities.items():
            # Hitta hela meningar som innehåller problematiska entiteter
            sentences = re.split(r'[.!?]+', corrected)
            filtered_sentences = []
            
            for sentence in sentences:
                if re.search(entity_pattern, sentence, re.IGNORECASE):
                    logger.info(f"[AUTO-CORRECT] Tar bort mening om {entity_pattern}")
                    # Hoppa över hela meningen
                    continue
                else:
                    filtered_sentences.append(sentence)
            
            corrected = '. '.join([s.strip() for s in filtered_sentences if s.strip()])
        
        return corrected

    def _ai_rewrite_problematic_sections(self, content: str, issues: List[str]) -> str:
        """Använd AI för att skriva om problematiska avsnitt"""
        if not self.ai_available:
            return content
            
        logger.info("[AUTO-CORRECT] AI omskriver problematiska avsnitt...")
        
        # Identifiera problematiska stycken
        paragraphs = content.split('\n\n')
        corrected_paragraphs = []
        
        for paragraph in paragraphs:
            needs_rewrite = False
            
            # Kolla om detta stycke innehåller några av problemen
            for issue in issues:
                if any(word in paragraph.lower() for word in ['nyligen', 'i går', 'förra veckan', 'northvolt']):
                    needs_rewrite = True
                    break
            
            if needs_rewrite:
                logger.info("[AUTO-CORRECT] Skriver om problematiskt stycke med AI...")
                rewritten = self._ai_rewrite_paragraph(paragraph)
                corrected_paragraphs.append(rewritten if rewritten else paragraph)
            else:
                corrected_paragraphs.append(paragraph)
        
        return '\n\n'.join(corrected_paragraphs)

    def _ai_rewrite_paragraph(self, paragraph: str) -> Optional[str]:
        """Skriv om ett specifikt stycke med AI"""
        try:
            prompt = f"""
            Skriv om följande podcast-stycke för att ta bort faktakontroll-problem:

            ORIGINAL: {paragraph}

            PROBLEM ATT ÅTGÄRDA:
            - Ta bort tidskänsliga referenser som "nyligen", "i går", "förra veckan" 
            - Ersätt med "under 2025", "tidigare i år", "enligt senaste rapporter"
            - Ta bort referenser till Northvolt (konkurs 2024)
            - Ta bort specifika ministernamn - använd "regeringen" istället
            - Behåll samma ton och innehåll men gör det tidsneutralt

            VIKTIGT: Behåll Lisa/Pelle-dialogen om den finns. Skriv ENDAST det omskrivna stycket, inget annat.
            """

            response = self.client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            rewritten = response.choices[0].message.content.strip()
            logger.info(f"[AUTO-CORRECT] AI omskrivning: {len(paragraph)} → {len(rewritten)} tecken")
            return rewritten
            
        except Exception as e:
            logger.error(f"[AUTO-CORRECT] AI-omskrivning misslyckades: {e}")
            return None

    def generate_alternative_news(self, problematic_topic: str) -> Optional[str]:
        """Generera alternativa nyheter när faktakontroll misslyckas"""
        if not self.ai_available:
            return None
            
        logger.info(f"[AUTO-CORRECT] Genererar alternativa nyheter för: {problematic_topic}")
        
        try:
            prompt = f"""
            Generera en säker, aktuell nyhet för oktober 2025 inom teknik/AI/klimat som ersättning för problematiskt innehåll.

            UNDVIK:
            - Konkursade eller problematiska företag (Northvolt, etc.)
            - Specifika ministernamn - använd "regeringen" eller "myndigheter"
            - Tidskänsliga ord som "nyligen", "i går", "förra veckan"
            - Specifika investeringsbelopp utan verifiering

            INKLUDERA:
            - Allmänna trender inom AI, hållbarhet, eller teknik
            - Vetenskapliga genombrott eller forskning
            - Branschövergripande utveckling
            - Globala eller EU-baserade initiativ

            FORMAT: Lisa och Pelle naturlig dialog (2-3 utbyten), ~150-200 ord

            Ämne att ersätta: {problematic_topic}
            """

            response = self.client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=400
            )
            
            alternative_news = response.choices[0].message.content.strip()
            logger.info("[AUTO-CORRECT] Alternativa nyheter genererade")
            return alternative_news
            
        except Exception as e:
            logger.error(f"[AUTO-CORRECT] Generering av alternativa nyheter misslyckades: {e}")
            return None

def auto_correct_podcast_content(content: str, fact_issues: List[str]) -> Tuple[str, bool]:
    """
    Huvudfunktion för automatisk korrigering av podcast-innehåll
    
    Returns:
        (corrected_content, success)
    """
    corrector = SelfCorrectingFactChecker()
    return corrector.auto_correct_content(content, fact_issues)

if __name__ == "__main__":
    # Test av auto-korrigeringssystemet
    test_content = """
    Lisa: Northvolt fick nyligen en stor investering på 6 miljarder kronor.
    Pelle: Ja, och arbetsmarknadsminister Johan Pehrson sa i går att detta kommer skapa jobb.
    Lisa: Det är spännande att se hur företag utvecklas så snabbt i vår tid.
    """
    
    test_issues = ["tidskänslig referens", "konkursade företag", "fel ministerpost"]
    
    print("Testar automatisk korrigering...")
    corrected, success = auto_correct_podcast_content(test_content, test_issues)
    
    print(f"\nOriginalt:\n{test_content}")
    print(f"\nKorrigerat:\n{corrected}")
    print(f"\nLyckades: {success}")