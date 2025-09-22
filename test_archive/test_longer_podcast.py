#!/usr/bin/env python3
"""
Test för att generera en längre podcast och se exakt vad som händer
"""

import sys
sys.path.append('.')
from emotion_analyzer import split_content_by_emotion

def test_longer_content():
    # Längre, mer realistiskt podcast-innehåll
    content = """Välkommen till Människa Maskin Miljö, vecka 38! Jag heter Sanna och tillsammans med George kommer vi berätta om veckans tekniknyheter.

Den här veckan har varit helt fantastisk med spännande genombrott inom artificiell intelligens. Forskare har utvecklat nya modeller som kan förstå mänskliga känslor på ett helt nytt sätt.

Vi har också fått allvarliga rapporter om cybersäkerhetshot som påverkar svenska företag. Det är viktigt att alla tar detta på allvar och förstärker sina säkerhetsrutiner.

Roliga nyheter kommer från tech-världen där nya gadgets gör vardagen enklare och mer miljövänlig. Det här visar hur innovation kan lösa verkliga problem.

För att avsluta vill vi dela med oss av forskning som visar hur automation och AI kan hjälpa oss nå klimatmålen. Det här är professionell utveckling som kommer påverka oss alla.

Det var allt för denna vecka. Tack för att ni lyssnade på Människa Maskin Miljö!"""

    print(f'📝 Analyserar podcast-innehåll ({len(content)} tecken)')
    segments = split_content_by_emotion(content)

    print(f'\n🎬 Resultat: {len(segments)} segment(s)')
    total_chars = 0
    
    for i, seg in enumerate(segments, 1):
        chars = len(seg['text'])
        total_chars += chars
        print(f'🎤 Segment {i}: {seg["voice_name"]} ({seg["emotion"]})')
        print(f'   Text ({chars} tecken): {seg["text"][:100]}...')
        print(f'   Settings: stability={seg["voice_settings"]["stability"]}, style={seg["voice_settings"]["style"]}')
        print()
    
    print(f'📊 Sammanfattning:')
    print(f'   Total text: {total_chars} tecken')
    print(f'   Genomsnitt per segment: {total_chars // len(segments)} tecken')
    
    # Uppskatta audio-längd (ca 150 ord/minut, 5 tecken/ord)
    estimated_words = total_chars / 5
    estimated_minutes = estimated_words / 150
    print(f'   Uppskattad längd: {estimated_minutes:.1f} minuter')

if __name__ == "__main__":
    test_longer_content()
