#!/usr/bin/env python3
"""
Uppdaterat test av premiäravsnitt - reviderat manus
"""

import os
import sys
sys.path.append('.')

from google_tts_backup import create_google_podcast_service_account

def create_premiar_med_musik():
    """Skapar premiäravsnittet med musik och uppdaterat manus"""
    
    # Sätt upp credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-service-account.json'
    
    # UPPDATERAT premiärmanus - utan tekniska detaljer, med nyhetexempel
    premiar_segments = [
        {
            "voice": "lisa",
            "text": "Hej och varmt välkomna till allra första avsnittet av MMM Senaste Nytt! Jag heter Lisa...",
            "music_before": {
                "file": "audio/music/088d314d.mp3",
                "duration": 20,  # 20 sek intro
                "fade_in": 2,
                "fade_out": 3
            }
        },
        {
            "voice": "pelle", 
            "text": "...och jag heter Pelle! Vi är glada över att kunna träffa er här i vår helt nya dagliga nyhetspod."
        },
        {
            "voice": "lisa",
            "text": "MMM Senaste Nytt är en spinoff från den etablerade podcasten Människa Maskin Miljö som fokuserar på hur teknik, innovation och mänskligt beteende påverkar vår planet."
        },
        {
            "voice": "pelle",
            "text": "Precis! Medan huvudpodden fördjupar sig i ämnen som elbilar, hållbar mat, och mobiltelefoners miljöpåverkan, så tar vi här i MMM Senaste Nytt reda på vad som händer just nu - varje dag.",
            "music_after": {
                "file": "audio/music/e5693973.mp3",
                "duration": 8,  # 8 sek brygga
                "volume": 0.3
            }
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
            "music_after": {
                "file": "audio/music/e5693973.mp3",
                "duration": 8,
                "volume": 0.3
            }
        },
        {
            "voice": "lisa",
            "text": "Transparens är viktigt för oss - vi anger alltid vilka källor våra nyheter kommer från så att ni kan läsa mer om det som intresserar er."
        },
        {
            "voice": "pelle",
            "text": "Och här kommer några exempel på vad ni kan förvänta er. I veckan har vi till exempel sett hur artificiell intelligens nu används för att optimera vindkraftsparker i Östersjön, vilket kan öka energiproduktionen med upp till 15 procent."
        },
        {
            "voice": "lisa",
            "text": "Det betyder mer nyheter, oftare, och alltid aktuellt! Igår rapporterade till exempel Reuters om ett genombrott inom batteriåtervinning som kan minska koboltbehovet med 70 procent. Sådana nyheter når er samma dag här hos oss."
        },
        {
            "voice": "pelle",
            "text": "Vare sig det handlar om genombrott inom förnybar energi, nya AI-modeller som kan hjälpa miljöarbetet, eller politiska beslut som påverkar klimatet - vi håller er uppdaterade.",
            "music_after": {
                "file": "audio/music/e5693973.mp3", 
                "duration": 8,
                "volume": 0.3
            }
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
            "music_after": {
                "file": "audio/music/9858802e.mp3",
                "duration": 25,  # 25 sek outro
                "fade_in": 3,
                "fade_out": 5
            }
        }
    ]
    
    print("🎙️ Skapar UPPDATERAT premiärtest med musik")
    print("=" * 50)
    print("🔧 ÄNDRINGAR:")
    print("   ❌ Borttaget: tekniska detaljer om TTS och kostnader")
    print("   ❌ Borttaget: överdrivna glädjeyttringar")
    print("   ✅ Tillagt: konkreta nyhetexempel")
    print("   ✅ Tillagt: musik (intro/bryggor/outro)")
    print()
    
    # Skapa tal-segmenten först
    result = create_google_podcast_service_account(premiar_segments)
    
    if result:
        print(f"\n✅ UPPDATERAT PREMIÄRTEST: {result}")
        print("\n🎧 Nu med:")
        print("   • Reviderat manus utan tekniska detaljer")
        print("   • Konkreta nyhetexempel istället")
        print("   • Naturligare dialogflöde")
        print("\n🎵 Musik som behöver läggas till manuellt:")
        print("   • Intro: 088d314d.mp3 (20 sek)")
        print("   • 3x Bryggor: e5693973.mp3 (8 sek vardera)")
        print("   • Outro: 9858802e.mp3 (25 sek)")
        
        return result
    else:
        print("\n❌ Fel vid skapandet av uppdaterat premiärtest")
        return None

if __name__ == "__main__":
    create_premiar_med_musik()