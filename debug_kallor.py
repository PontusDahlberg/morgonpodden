#!/usr/bin/env python3
"""
Debug källsystem för att se varför länkar saknas
"""
import json
import logging
from run_podcast_complete import generate_structured_podcast_content

# Konfigurera logging för att se vad som händer
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_kallor():
    """Debug varför källor inte syns i RSS"""
    try:
        print("🔍 DEBUGGAR KÄLLSYSTEM...")
        
        # Kolla scraped_content.json först
        try:
            with open('scraped_content.json', 'r', encoding='utf-8') as f:
                scraped_data = json.load(f)
            print(f"📁 scraped_content.json: {len(scraped_data)} källgrupper")
            
            for i, source_group in enumerate(scraped_data[:3]):
                source_name = source_group.get('source', 'Okänd')
                items_count = len(source_group.get('items', []))
                print(f"  {i+1}. {source_name}: {items_count} artiklar")
                
                # Visa första artikeln om den finns
                if source_group.get('items'):
                    first_item = source_group['items'][0]
                    title = first_item.get('title', 'Ingen titel')[:60]
                    link = first_item.get('link', 'INGEN LÄNK')
                    print(f"     Första artikel: {title}...")
                    print(f"     Länk: {link}")
                print()
                
        except Exception as e:
            print(f"❌ Fel vid läsning av scraped_content.json: {e}")
        
        # Test med enkel väderinfo
        weather_info = 'Vädret idag: varierande molnighet'
        
        # Anropa funktionen och se vad som händer med källor
        print("🎯 TESTAR generate_structured_podcast_content...")
        content, articles = generate_structured_podcast_content(weather_info)
        
        print(f"📊 RESULTAT:")
        print(f"   Antal artiklar efter filtrering: {len(articles)}")
        
        if articles:
            for i, article in enumerate(articles[:5]):
                source = article.get('source', 'N/A')
                title = article.get('title', 'N/A')[:50]
                link = article.get('link', 'SAKNAS')
                print(f"   {i+1}. {source}")
                print(f"      Titel: {title}...")
                print(f"      Länk: {link}")
                print()
        else:
            print("   ❌ INGA ARTIKLAR HITTADES!")
            
    except Exception as e:
        print(f"❌ Fel i debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_kallor()