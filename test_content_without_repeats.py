#!/usr/bin/env python3
# Test för att se vad som händer utan upprepningar

import json
import logging

# Konfigurera logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def test_new_content():
    """
    Simulera innehåll som skulle komma om vi hade nya artiklar
    """
    
    # Relevant innehåll som skulle kunna komma
    simulated_articles = [
        {
            "source": "Ny Teknik",
            "title": "Svenska forskare utvecklar ny AI för klimatmodellering",
            "content": "Forskare vid KTH har utvecklat en AI-modell som kan förutsäga klimatförändringar med 95% noggrannhet",
            "link": "https://nyteknik.se/ai-klimat-2025"
        },
        {
            "source": "Computer Sweden", 
            "title": "Microsoft lanserar koldioxidneutral datacenter i Sverige",
            "content": "Nya datacentret i Sandviken drivs helt på förnybar energi och använder avancerad kylning",
            "link": "https://computersweden.se/microsoft-datacenter-2025"
        },
        {
            "source": "Miljö & Utveckling",
            "title": "EU:s nya batteridirektiv träder i kraft",
            "content": "Från 2026 måste alla batterier i EU innehålla minst 50% återvunnet material",
            "link": "https://miljo-utveckling.se/eu-batteridirektiv-2026"
        },
        {
            "source": "European Environment Agency",
            "title": "EEA rapport: Europas luftkvalitet förbättras markant", 
            "content": "Nya mätningar visar att PM2.5-partiklar minskat med 30% sedan 2019",
            "link": "https://eea.europa.eu/air-quality-report-2025"
        }
    ]
    
    print("🆕 SIMULERADE NYA ARTIKLAR (utan upprepningar):")
    print(f"📊 Antal artiklar: {len(simulated_articles)}")
    print("\nInnehåll:")
    
    for i, article in enumerate(simulated_articles, 1):
        print(f"{i}. {article['source']}")
        print(f"   Titel: {article['title']}")
        print(f"   Länk: {article['link']}")
        print()
    
    # Kontrollera balansen
    ai_tech = sum(1 for a in simulated_articles if any(keyword in (a['title'] + ' ' + a['content']).lower() 
                                                      for keyword in ['ai', 'teknologi', 'datacenter', 'microsoft']))
    climate = sum(1 for a in simulated_articles if any(keyword in (a['title'] + ' ' + a['content']).lower() 
                                                       for keyword in ['klimat', 'miljö', 'koldioxid', 'förnybar', 'batterier']))
    
    print(f"📈 INNEHÅLLSBALANS:")
    print(f"🤖 AI/Teknik: {ai_tech} artiklar")
    print(f"🌱 Klimat/Miljö: {climate} artiklar")
    
    if ai_tech == climate:
        print("✅ PERFEKT BALANS!")
    elif ai_tech > climate:
        print("⚠️ Lite för mycket teknik, behöver mer klimat")
    else:
        print("⚠️ Lite för mycket klimat, behöver mer teknik")

if __name__ == "__main__":
    test_new_content()