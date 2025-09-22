#!/usr/bin/env python3
"""
Test för att visa exakt hur emotion-analysen fungerade för den genererade podcasten
"""

import sys
sys.path.append('.')
from emotion_analyzer import split_content_by_emotion

def test_generated_content():
    
    # Simulera liknande innehåll som genererades
    test_content = """Välkommen till Människa Maskin Miljö, vecka 38! 

Den här veckan har vi spännande utvecklingar inom AI och teknologi som påverkar vår vardag på olika sätt.

Forskare har gjort viktiga upptäckter som kan förändra hur vi arbetar med miljöteknik.

Vi har också roliga nyheter om utveckling inom automation och hållbar teknik.

Detta visar hur teknologi och miljötänk kan kombineras för framtidens lösningar."""
    
    print('📝 Analyserar genererat innehåll:')
    print(f'Total längd: {len(test_content)} tecken\n')
    
    segments = split_content_by_emotion(test_content)
    
    for i, segment in enumerate(segments, 1):
        print(f'🎤 Segment {i}: {segment["voice_name"]} ({segment["emotion"]})')
        print(f'   Inställningar: stability={segment["voice_settings"]["stability"]}, style={segment["voice_settings"]["style"]}')
        print(f'   Text: "{segment["text"][:80]}..."')
        print()
    
    print(f'✅ Totalt {len(segments)} segment(s) genererade')
    print(f'📊 Emotion-fördelning:')
    
    emotions = [seg["emotion"] for seg in segments]
    for emotion in set(emotions):
        count = emotions.count(emotion)
        print(f'   {emotion}: {count} segment(s)')

if __name__ == "__main__":
    test_generated_content()
