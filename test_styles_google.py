#!/usr/bin/env python3
"""
Test av Google Cloud TTS med styles från det gamla manuset
"""

import os
import sys
sys.path.append('.')

from google_tts_backup import create_google_podcast_service_account

def test_styles_med_google_tts():
    """Testar om Google Cloud TTS kan hantera styles eller läser upp dem"""
    
    # Sätt upp credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-service-account.json'
    
    # Test-segment med styles från det gamla manuset
    test_segments = [
        {
            "voice": "lisa",  # Använd Lisa som Anna
            "text": "[friendly] God kväll och varmt välkommen till MMM Senaste Nytt! Jag är Lisa och tillsammans med mig har jag min kollega Pelle."
        },
        {
            "voice": "pelle",  # Använd Pelle som Erik
            "text": "[friendly] Hej allihop! Skönt att vara här en torsdagskväll."
        },
        {
            "voice": "lisa",
            "text": "[excited] Och vi har ett riktigt spännande program ikväll! Det har hänt en hel del i teknikvärlden den här veckan."
        },
        {
            "voice": "pelle",
            "text": "[curious] Absolut, speciellt nyheten om svenska AI-bolaget som har sålt för tio miljarder kronor."
        },
        {
            "voice": "lisa",
            "text": "[surprised] Det är verkligen imponerande! Men vad händer egentligen när Google Cloud TTS läser upp dessa style-taggar?"
        },
        {
            "voice": "pelle",
            "text": "[concerned] Ja, det är ju frågan - kommer den att säga ordet 'concerned' eller förstå att jag ska låta bekymrad?"
        },
        {
            "voice": "lisa",
            "text": "[laughing] Vi får se om jag verkligen låter som om jag skrattar nu, eller om jag bara säger ordet 'laughing'!"
        }
    ]
    
    print("🧪 TESTAR: Google Cloud TTS med ElevenLabs-styles")
    print("=" * 55)
    print("📝 TESTFRÅGA: Läser Google Cloud TTS upp style-taggarna som text?")
    print("    Exempel: Säger Lisa '[friendly]' eller låter hon vänlig?")
    print()
    print("🎤 TESTSEGMENT:")
    for i, segment in enumerate(test_segments, 1):
        style = segment["text"].split(']')[0] + ']' if '[' in segment["text"] else 'ingen style'
        print(f"   {i}. {segment['voice']}: {style}")
    print()
    
    # Skapa podcast med style-tester
    result = create_google_podcast_service_account(test_segments)
    
    if result:
        print(f"\n✅ STYLE-TEST KLAR: {result}")
        print("\n🎧 LYSSNA OCH BEDÖM:")
        print("   ❓ Läser rösterna upp '[friendly]' som text?") 
        print("   ❓ Eller ignoreras style-taggarna helt?")
        print("   ❓ Finns det någon skillnad i tonfall?")
        print("\n💡 SLUTSATS:")
        print("   • Om de läser upp taggarna = vi måste rensa bort dem")
        print("   • Om de ignoreras = vi kan behålla dem (gör inget)")
        print("   • Om de påverkar tonfall = fantastiskt!")
        
        return result
    else:
        print("\n❌ Kunde inte skapa style-test")
        return None

if __name__ == "__main__":
    test_styles_med_google_tts()