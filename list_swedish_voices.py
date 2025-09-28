#!/usr/bin/env python3
"""
Lista alla tillgängliga svenska röster i Google Cloud TTS
"""

import os
from google.cloud import texttospeech

def list_all_swedish_voices():
    """Lista alla tillgängliga svenska röster"""
    
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        print("⚠️ GOOGLE_APPLICATION_CREDENTIALS saknas")
        return
    
    try:
        client = texttospeech.TextToSpeechClient()
        
        # Hämta alla tillgängliga röster
        voices = client.list_voices()
        
        print("🔍 Alla tillgängliga svenska röster:")
        print("=" * 60)
        
        swedish_voices = []
        
        for voice in voices.voices:
            # Filtrera på svenska språkkoder
            for language_code in voice.language_codes:
                if language_code.startswith('sv-'):
                    swedish_voices.append({
                        'name': voice.name,
                        'language': language_code,
                        'gender': voice.ssml_gender.name,
                        'natural_rate': voice.natural_sample_rate_hertz
                    })
        
        # Sortera på namn
        swedish_voices.sort(key=lambda x: x['name'])
        
        if not swedish_voices:
            print("❌ Inga svenska röster hittades")
            return
        
        print(f"Hittade {len(swedish_voices)} svenska röster:\n")
        
        categories = {
            'Standard': [],
            'Wavenet': [],
            'Neural2': [],
            'Studio': [],
            'Journey': [],
            'Polyglot': [],
            'Andra': []
        }
        
        # Kategorisera rösterna
        for voice in swedish_voices:
            name = voice['name']
            if 'Standard' in name:
                categories['Standard'].append(voice)
            elif 'Wavenet' in name:
                categories['Wavenet'].append(voice)
            elif 'Neural2' in name:
                categories['Neural2'].append(voice)
            elif 'Studio' in name:
                categories['Studio'].append(voice)
            elif 'Journey' in name:
                categories['Journey'].append(voice)
            elif 'Polyglot' in name:
                categories['Polyglot'].append(voice)
            else:
                categories['Andra'].append(voice)
        
        # Visa kategoriserat
        for category, voices_list in categories.items():
            if voices_list:
                print(f"📂 {category} röster:")
                for voice in voices_list:
                    quality_indicator = "🔊" if category in ['Neural2', 'Studio', 'Journey'] else "🎵"
                    print(f"   {quality_indicator} {voice['name']}")
                    print(f"      Språk: {voice['language']}")
                    print(f"      Kön: {voice['gender']}")
                    print(f"      Frekvens: {voice['natural_rate']} Hz")
                    print()
        
        # Rekommendationer
        print("💡 REKOMMENDATIONER för podcast:")
        print("=" * 40)
        
        best_female = None
        best_male = None
        
        # Prioritera ordning: Studio > Neural2 > Journey > Wavenet > Standard
        priority_order = ['Studio', 'Neural2', 'Journey', 'Wavenet', 'Standard']
        
        for category in priority_order:
            for voice in categories[category]:
                if voice['gender'] == 'FEMALE' and not best_female:
                    best_female = voice
                if voice['gender'] == 'MALE' and not best_male:
                    best_male = voice
                if best_female and best_male:
                    break
            if best_female and best_male:
                break
        
        if best_female:
            print(f"🎭 BÄSTA KVINNLIG RÖST: {best_female['name']}")
        if best_male:
            print(f"🎭 BÄSTA MANLIG RÖST: {best_male['name']}")
            
    except Exception as e:
        print(f"❌ Fel: {e}")

if __name__ == "__main__":
    list_all_swedish_voices()
