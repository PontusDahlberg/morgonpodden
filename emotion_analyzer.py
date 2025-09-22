#!/usr/bin/env python3
"""
Intelligent style selector för podcast-innehåll
Analyserar text och väljer lämplig ElevenLabs style
"""

import re
import os
import requests
from typing import Dict, List, Tuple

def analyze_content_emotion(text: str) -> str:
    """
    Analysera textinnehåll och bestäm lämplig emotional style
    """
    text_lower = text.lower()
    
    # Definiera nyckelord för olika emotioner
    emotion_keywords = {
        'exciting': [
            'genombrott', 'revolution', 'fantastisk', 'otrolig', 'banbrytande', 
            'spännande', 'imponerande', 'framsteg', 'innovation', 'framtid',
            'rekord', 'första gången', 'historisk', 'milstolpe'
        ],
        'serious': [
            'klimatkris', 'fara', 'hot', 'varning', 'problem', 'kris', 
            'allvarlig', 'bekymmer', 'risk', 'konsekvens', 'kritisk',
            'förstörelse', 'katastrofal', 'akut', 'brådskande'
        ],
        'friendly': [
            'hjälpa', 'förbättra', 'utveckling', 'lösning', 'möjlighet',
            'samarbete', 'gemenskap', 'positiv', 'hållbar', 'framtid',
            'tillsammans', 'stöd', 'välkomna', 'trevlig'
        ],
        'professional': [
            'forskning', 'studie', 'rapport', 'analys', 'data', 'resultat',
            'undersökning', 'experter', 'vetenskaplig', 'statistik',
            'mätning', 'bevis', 'fakta', 'objektiv'
        ]
    }
    
    # Räkna träffar för varje emotion
    emotion_scores = {}
    for emotion, keywords in emotion_keywords.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        emotion_scores[emotion] = score
    
    # Hitta dominant emotion
    if not any(emotion_scores.values()):
        return 'professional'  # Default
    
    dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
    return dominant_emotion

def get_voice_settings_for_emotion(emotion: str) -> Dict:
    """
    Returnera ElevenLabs voice settings baserat på emotion
    """
    emotion_settings = {
        'exciting': {
            'stability': 0.2,           # Låg för mycket variation
            'similarity_boost': 0.8,    # Hög för röstlikhet
            'style': 0.8,              # Hög för mycket uttryck
            'use_speaker_boost': True
        },
        'serious': {
            'stability': 0.7,           # Hög för stabil, allvarlig ton
            'similarity_boost': 0.9,    # Max för tydlighet
            'style': 0.3,              # Låg för kontrollerad känsla
            'use_speaker_boost': True
        },
        'friendly': {
            'stability': 0.4,           # Måttlig för naturlig variation
            'similarity_boost': 0.85,   # Hög för varm känsla
            'style': 0.6,              # Måttlig för vänlig ton
            'use_speaker_boost': True
        },
        'professional': {
            'stability': 0.5,           # Balanserad för nyhetston
            'similarity_boost': 0.85,   # Hög för klarhet
            'style': 0.5,              # Måttlig för professionell känsla
            'use_speaker_boost': True
        }
    }
    
    return emotion_settings.get(emotion, emotion_settings['professional'])

def split_content_by_emotion(text: str) -> List[Dict]:
    """
    Dela upp text i segment baserat på innehåll och välj rätt emotion/röst för varje
    Säkerställer balanserad fördelning mellan Sanna och George
    """
    # Enkel uppdelning på stycken först
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    segments = []
    sanna_voice = os.getenv('ELEVENLABS_VOICE_ID_SANNA')
    george_voice = os.getenv('ELEVENLABS_VOICE_ID_GEORGE')
    
    # Beräkna taltid per stycke för balansering
    paragraph_lengths = [len(p) for p in paragraphs]
    total_length = sum(paragraph_lengths)
    
    # Håll räkning på fördelning
    sanna_time = 0
    george_time = 0
    
    for i, paragraph in enumerate(paragraphs):
        if not paragraph:
            continue
            
        paragraph_length = len(paragraph)
        
        # Analysera emotion för detta stycke
        emotion = analyze_content_emotion(paragraph)
        
        # Beräkna vem som behöver mer taltid
        sanna_ratio = sanna_time / total_length if total_length > 0 else 0
        george_ratio = george_time / total_length if total_length > 0 else 0
        
        # Grundläggande alternering, men justera för balans
        should_be_sanna = i % 2 == 0
        
        # Justera baserat på nuvarande balans
        if sanna_ratio > 0.6:  # Sanna har för mycket tid
            should_be_sanna = False
        elif george_ratio > 0.6:  # George har för mycket tid  
            should_be_sanna = True
        
        # Särskilda regler för första och sista segmenten
        if i == 0:  # Första segmentet - välkomst
            should_be_sanna = True  # Sanna hälsar välkommen
        elif i == len(paragraphs) - 1:  # Sista segmentet - avslutning
            # Växla från vem som hade föregående segment
            should_be_sanna = not (segments[-1]['voice_name'] == 'Sanna')
        
        # Tilldela röst
        if should_be_sanna:
            voice_id = sanna_voice
            voice_name = 'Sanna'
            sanna_time += paragraph_length
        else:
            voice_id = george_voice  
            voice_name = 'George'
            george_time += paragraph_length
        
        segments.append({
            'text': paragraph,
            'voice_id': voice_id,
            'voice_name': voice_name,
            'emotion': emotion,
            'voice_settings': get_voice_settings_for_emotion(emotion)
        })
        
    # Debug-information om fördelning
    final_sanna_ratio = sanna_time / total_length if total_length > 0 else 0
    final_george_ratio = george_time / total_length if total_length > 0 else 0
    
    print(f"🎭 Röstfördelning: Sanna {final_sanna_ratio:.1%}, George {final_george_ratio:.1%}")
    
    return segments
    
    return segments

def test_emotion_analysis():
    """
    Testa emotion analysis med olika typer av innehåll
    """
    test_texts = [
        {
            'text': 'Forskare har gjort ett fantastiskt genombrott inom AI som kan revolutionera hur vi bekämpar klimatförändringarna!',
            'expected': 'exciting'
        },
        {
            'text': 'Ny rapport varnar för allvarliga konsekvenser av klimatkrisen. Experter menar att situationen är kritisk.',
            'expected': 'serious'
        },
        {
            'text': 'Studien visar att ny teknologi kan hjälpa oss att tillsammans skapa en mer hållbar framtid.',
            'expected': 'friendly'
        },
        {
            'text': 'Forskningsresultaten från universitetet visar statistiska data om energieffektivitet.',
            'expected': 'professional'
        }
    ]
    
    print("🧠 Testar emotion analysis:")
    print("=" * 50)
    
    for i, test in enumerate(test_texts):
        detected = analyze_content_emotion(test['text'])
        expected = test['expected']
        status = "✅" if detected == expected else "❌"
        
        print(f"\nTest {i+1}: {status}")
        print(f"Text: {test['text'][:60]}...")
        print(f"Förväntad: {expected}")
        print(f"Upptäckt: {detected}")
        
        if detected != expected:
            print(f"⚠️ Felaktig klassificering!")

if __name__ == "__main__":
    test_emotion_analysis()
