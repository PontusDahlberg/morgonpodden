#!/usr/bin/env python3
"""
Skapar premiär med nya låtar och fixade texter
"""

import os
import sys
sys.path.append('.')

from google_tts_backup import create_google_podcast_service_account

def create_premiar_ny_musik():
    """Skapar premiäravsnittet med nya låtar och fixat manus"""
    
    # Sätt upp credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-service-account.json'
    
    # FIXAT premiärmanus - utan punkter
    premiar_segments = [
        {
            "voice": "lisa",
            "text": "Hej och varmt välkomna till allra första avsnittet av MMM Senaste Nytt! Jag heter Lisa"
        },
        {
            "voice": "pelle", 
            "text": "och jag heter Pelle! Vi är glada över att kunna träffa er här i vår helt nya dagliga nyhetspod."
        },
        {
            "voice": "lisa",
            "text": "MMM Senaste Nytt är en spinoff från den etablerade podcasten Människa Maskin Miljö som fokuserar på hur teknik, innovation och mänskligt beteende påverkar vår planet."
        },
        {
            "voice": "pelle",
            "text": "Precis! Medan huvudpodden fördjupar sig i ämnen som elbilar, hållbar mat, och mobiltelefoners miljöpåverkan, så tar vi här i MMM Senaste Nytt reda på vad som händer just nu - varje dag."
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
            "text": "Våra källor kommer från svenska medier som SVT, DN och SvD, europeiska nyhetskällor som Euronews och Politico Europe, samt internationella giganter som BBC och Reuters."
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
            "text": "Vare sig det handlar om genombrott inom förnybar energi, nya AI-modeller som kan hjälpa miljöarbetet, eller politiska beslut som påverkar klimatet - vi håller er uppdaterade."
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
            "text": "Ha det bra tills dess!"
        }
    ]
    
    print("🎙️ Skapar FIXAT premiärtest")
    print("=" * 40)
    print("🔧 FIXAT:")
    print("   ❌ Borttaget: punkter (...) från Lisa/Pelle intro")
    print("   ✅ Snygg överlämning utan märkliga punkter")
    print("🎵 NYA LÅTAR:")
    print("   🎼 Intro: 'Mellan Dröm och Verklighet' (15 sek)")
    print("   🎼 Outro: 'MMM Senaste Nytt...' (60 sek med fade out)")
    print()
    
    # Skapa tal-segmenten
    result = create_google_podcast_service_account(premiar_segments)
    
    if result:
        print(f"\n✅ FIXAT RÖSTSPÅR: {result}")
        print("\n🎵 Nästa steg: Mixa med nya låtar")
        print("   • Intro: 'audio/music/Mellan Dröm och Verklighet.mp3'")
        print("   • Outro: 'audio/music/MMM Senaste Nytt Från Människa Maskin Mi.mp3'")
        
        return result
    else:
        print("\n❌ Fel vid skapandet av röstspår")
        return None

if __name__ == "__main__":
    create_premiar_ny_musik()