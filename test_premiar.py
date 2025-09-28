#!/usr/bin/env python3
"""
Test av premiäravsnitt för MMM Senaste Nytt
Använder befintlig musik som placeholder för intro/bryggor/outro
"""

import os
import sys
sys.path.append('.')

from google_tts_backup import create_google_podcast_service_account

def create_premiar_test():
    """Skapar ett test av premiäravsnittet med befintlig musik"""
    
    # Sätt upp credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-service-account.json'
    
    # Premiärmanus uppdelat i segment
    premiar_segments = [
        {
            "voice": "lisa",
            "text": "Hej och varmt välkomna till allra första avsnittet av MMM Senaste Nytt! Jag heter Lisa...",
            "music_intro": "audio/music/088d314d.mp3"  # Intro musik
        },
        {
            "voice": "pelle", 
            "text": "...och jag heter Pelle! Vi är så glada över att få träffa er här i vår helt nya dagliga nyhetspod."
        },
        {
            "voice": "lisa",
            "text": "MMM Senaste Nytt är en spinoff från den etablerade podcasten Människa Maskin Miljö som fokuserar på hur teknik, innovation och mänskligt beteende påverkar vår planet."
        },
        {
            "voice": "pelle",
            "text": "Precis! Medan huvudpodden fördjupar sig i ämnen som elbilar, hållbar mat, och mobiltelefoners miljöpåverkan, så tar vi här i MMM Senaste Nytt reda på vad som händer just nu - varje dag.",
            "music_bridge": "audio/music/e5693973.mp3"  # Brygga musik
        },
        {
            "voice": "lisa",
            "text": "Varje dag, måndag till söndag, levererar vi tio minuter med de viktigaste nyheterna inom våra tre kärnområden: Människa, Maskin och Miljö."
        },
        {
            "voice": "pelle",
            "text": "Vi följer utvecklingen inom artificiell intelligens och dess roll i klimatarbetet, nya tekniska lösningar för att minska utsläpp, och hur samhället anpassar sig till klimatförändringarna."
        },
        {
            "voice": "lisa",
            "text": "Men vi glömmer inte bort den mänskliga faktorn - hur påverkar ny teknik våra liv, våra jobb, och våra möjligheter att leva mer hållbart?"
        },
        {
            "voice": "pelle",
            "text": "Våra källor kommer från svenska medier som SVT, DN och SvD, europeiska nyhetskällor som Euronews och Politico Europe, samt internationella giganter som BBC och Reuters.",
            "music_bridge": "audio/music/e5693973.mp3"  # Brygga musik
        },
        {
            "voice": "lisa",
            "text": "Transparens är viktigt för oss - vi anger alltid vilka källor våra nyheter kommer från så att ni kan läsa mer om det som intresserar er."
        },
        {
            "voice": "pelle",
            "text": "Och här är det coola - tack vare ny teknik kan vi nu sända dagligen istället för bara en gång i veckan! Vi använder Google Cloud TTS med svenska Chirp3-HD röster, vilket ger oss fantastisk kvalitet till en bråkdel av tidigare kostnader."
        },
        {
            "voice": "lisa",
            "text": "Det betyder mer nyheter, oftare, och alltid aktuellt! Ingen väntan på veckans sammanfattning - här får ni veta vad som händer samma dag."
        },
        {
            "voice": "pelle",
            "text": "Vare sig det handlar om genombrott inom förnybar energi, nya AI-modeller som kan hjälpa miljöarbetet, eller politiska beslut som påverkar klimatet - vi håller er uppdaterade.",
            "music_bridge": "audio/music/e5693973.mp3"  # Brygga musik
        },
        {
            "voice": "lisa",
            "text": "Så vad kan ni förvänta er framöver? Måndag till fredag fokuserar vi på veckans stora nyheter och utvecklingar. Helger blir mer reflekterande med djupare analys."
        },
        {
            "voice": "pelle",
            "text": "Och glöm inte bort att prenumerera på vår huvudpodcast Människa Maskin Miljö för djupare dykningar i dessa ämnen - där tar vi oss tid att verkligen utforska hur allt hänger ihop."
        },
        {
            "voice": "lisa",
            "text": "Vi på MMM Senaste Nytt kommer här varje dag, samma tid, med nyheter som formar vår framtid. För det är just det det handlar om - hur vi tillsammans navigerar i en värld där teknik, mänsklighet och miljö ständigt påverkar varandra."
        },
        {
            "voice": "pelle",
            "text": "Så välkomna till MMM Senaste Nytt! Vi ses här imorgon med dagens viktigaste nyheter från världen av människa, maskin och miljö."
        },
        {
            "voice": "lisa",
            "text": "Ha det bra tills dess!",
            "music_outro": "audio/music/9858802e.mp3"  # Outro musik
        }
    ]
    
    print("🎙️ Skapar TEST av MMM Senaste Nytt - Premiäravsnitt")
    print("=" * 55)
    print("📝 Använder befintlig musik som placeholder:")
    print("   🎵 Intro: 088d314d.mp3 (mysterious, calm)")
    print("   🎵 Bryggor: e5693973.mp3 (serious, dramatic)") 
    print("   🎵 Outro: 9858802e.mp3 (weather, outro)")
    print()
    
    # Skapa endast tal-segmenten för nu (musik behöver separata verktyg)
    result = create_google_podcast_service_account(premiar_segments)
    
    if result:
        print(f"\n✅ PREMIÄR-TEST KLART! Audio sparad: {result}")
        print("\n🎧 Lyssna på resultatet för att höra:")
        print("   • Lisa och Pelles röster i premiärmanuset")
        print("   • Timing och flyt mellan segmenten") 
        print("   • Innehåll och struktur")
        print("\n📌 NOTERA: Detta är utan musik - den behöver läggas till separat")
        print("🎵 Musikbehov:")
        print("   • Intro: 15-20 sek (energisk)")
        print("   • 3x Bryggor: 5-8 sek (mjuka övergångar)")
        print("   • Outro: 20-25 sek (memorable)")
        
        return result
    else:
        print("\n❌ Något gick fel vid skapandet av premiärtestet")
        return None

if __name__ == "__main__":
    create_premiar_test()