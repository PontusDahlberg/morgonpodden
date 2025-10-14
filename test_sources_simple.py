#!/usr/bin/env python3
"""
Enkel test av källsystemet utan emojis
"""
import json
from run_podcast_complete import generate_structured_podcast_content

def test_sources():
    try:
        print("TESTAR KALLSYSTEM...")
        weather_info = 'Vadret idag: varierande molnighet'
        content, articles = generate_structured_podcast_content(weather_info)
        
        print(f"Antal artiklar: {len(articles)}")
        
        if articles:
            for i, article in enumerate(articles[:3]):
                source = article.get('source', 'N/A')
                title = article.get('title', 'N/A')[:60]
                link = article.get('link', 'SAKNAS')
                print(f"{i+1}. {source}")
                print(f"   Titel: {title}...")
                print(f"   Lank: {link}")
                print()
                
            print("RESULTAT: KALLOR FUNGERAR!")
            return True
        else:
            print("RESULTAT: INGA KALLOR HITTADES!")
            return False
            
    except Exception as e:
        print(f"FEL: {e}")
        return False

if __name__ == "__main__":
    test_sources()