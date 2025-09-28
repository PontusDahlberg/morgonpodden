#!/usr/bin/env python3
"""
Debug script för att testa AI-generering och text-rensning
"""

import sys
import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

def clean_script_text(text: str) -> str:
    """Rensa manus-text från stage directions och karaktärsnamn"""
    print("🧹 FÖRE text-rensning:")
    print("-" * 50)
    print(text[:500] + "..." if len(text) > 500 else text)
    print("-" * 50)
    
    original_text = text
    
    # Ta bort manus-headers och metadata
    text = re.sub(r'\[.*?\]', '', text)  # [PODCAST-MANUS: ...] 
    text = re.sub(r'---.*?---', '', text, flags=re.DOTALL)  # --- metadata ---
    
    # Ta bort karaktärsnamn i början av meningar
    text = re.sub(r'^(Sanna|George):\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n(Sanna|George):\s*', '\n', text)
    
    # Ta bort stage directions i parenteser
    text = re.sub(r'\([^)]*\)', '', text)
    
    # Ta bort karaktärsnamn följt av colon mitt i text
    text = re.sub(r'\b(Sanna|George):\s*', '', text)
    
    # Rensa extra whitespace och tomma rader
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Max 2 newlines
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)  # Leading spaces
    text = text.strip()
    
    print("🧹 EFTER text-rensning:")
    print("-" * 50)
    print(text[:500] + "..." if len(text) > 500 else text)
    print("-" * 50)
    print(f"Längd: {len(original_text)} → {len(text)} tecken")
    
    # Räkna stycken
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    print(f"Antal stycken: {len(paragraphs)}")
    
    return text

def test_ai_generation():
    """Testa AI-generering med debug output"""
    
    # Mock news för test
    news_summary = """- AI breakthrough (TechCrunch): New AI model released
- Climate tech advances (SVT): Green energy progress
- Cybersecurity alert (DN): Swedish companies at risk"""
    
    week_info = {'week': 38, 'year': 2025}
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ No API key found")
        return
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://manniska-maskin-miljo.com',
        'X-Title': 'Människa Maskin Miljö Podcast'
    }
    
    prompt = f"""Du är värd för den svenska podcasten "Människa Maskin Miljö" som fokuserar på teknik, AI och miljö.

Skapa ett engagerande podcast-manus för vecka {week_info['week']}, {week_info['year']} baserat på dessa nyheter:

{news_summary}

VIKTIGT - Skriv ENDAST ren taltext utan:
- Inga namn på talare (som "Sanna:", "George:")
- Inga stage directions (som "(entusiastiskt)", "(allvarlig ton)")
- Inga manus-markeringar eller rubriker
- Bara ren text som ska läsas upp

Krav för manuset:
- Skriv på svenska
- Börja med välkomst: "Välkommen till Människa Maskin Miljö, vecka {week_info['week']}!"
- Skriv som en sammanhängande berättelse utan karaktärsnamn
- Variera tonen naturligt: professionell, spännande, allvarlig eller vänlig
- Dela upp i naturliga stycken (5-8 stycken) för röstväxling
- Avsluta med "Det var allt för denna vecka. Tack för att ni lyssnade!"
- Totalt cirka 3-4 minuter läsning (2000-2500 ord)

Exempel på rätt format:
Välkommen till Människa Maskin Miljö, vecka 38!

Den här veckan har vi spännande utvecklingar inom artificiell intelligens...

Nu kommer vi till mer allvarliga nyheter om cybersäkerhet...

Fokusera på svenska nyheter och koppla till miljö/teknik-perspektiv även för internationella nyheter."""

    payload = {
        'model': 'anthropic/claude-3.5-sonnet',
        'messages': [
            {'role': 'user', 'content': prompt}
        ],
        'max_tokens': 3000,
        'temperature': 0.7
    }
    
    print("🤖 Anropar OpenRouter API...")
    
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_content = result['choices'][0]['message']['content']
            
            print("✅ AI-svar mottaget")
            print(f"Ursprunglig längd: {len(ai_content)} tecken")
            
            # Testa text-rensning
            cleaned_content = clean_script_text(ai_content)
            
            # Spara för analys
            with open('debug_original.txt', 'w', encoding='utf-8') as f:
                f.write(ai_content)
            with open('debug_cleaned.txt', 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            print("💾 Sparat som debug_original.txt och debug_cleaned.txt")
            
        else:
            print(f"❌ API error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_ai_generation()
