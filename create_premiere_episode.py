#!/usr/bin/env python3
"""
Skapa premiäravsnitt med Chirp3-HD röster (Gacrux = Lisa, Charon = Pelle)
Genererar rena röstfiler utan musik för import i Audacity
"""

import os
from google.cloud import texttospeech
import time

# Set up Google Cloud credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-service-account.json'

def create_premiere_episode():
    """Skapar premiäravsnitt med optimerade Chirp3-HD röster"""
    
    client = texttospeech.TextToSpeechClient()
    
    # Röstdefinitioner - optimerade från våra tester
    lisa_voice = texttospeech.VoiceSelectionParams(
        language_code="sv-SE",
        name="sv-SE-Chirp3-HD-Gacrux",  # Best female voice from tests
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    
    pelle_voice = texttospeech.VoiceSelectionParams(
        language_code="sv-SE", 
        name="sv-SE-Chirp3-HD-Charon",  # Best male voice from tests
        ssml_gender=texttospeech.SsmlVoiceGender.MALE
    )
    
    # Audio config - optimerad för podcast-kvalitet
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.0,  # Normal hastighet
        pitch=0.0,  # Normal tonhöjd
    )
    
    # Alla repliker från manuset - helt rena texter
    dialogue = [
        ("Lisa", "Hej och varmt välkomna till allra första avsnittet av MMM Senaste Nytt! Jag heter Lisa"),
        ("Pelle", "och jag heter Pelle! Vi är glada över att kunna träffa er här i vår helt nya dagliga nyhetspod."),
        ("Lisa", "MMM Senaste Nytt är en spinoff från den etablerade podcasten Människa Maskin Miljö som fokuserar på hur teknik, innovation och mänskligt beteende påverkar vår planet."),
        ("Pelle", "Precis! Medan huvudpodden fördjuper sig i ämnen som elbilar, hållbar mat, mobiltelefoners miljöpåverkan och klimatförändringarnas påverkan på allt och alla, så tar vi här i MMM Senaste Nytt reda på vad som händer just nu. Varje dag."),
        ("Lisa", "Ja Pelle, det stämmer: Varje dag, måndag till söndag, levererar vi tio minuter med de viktigaste nyheterna inom våra tre kärnområden: Människa, Maskin och Miljö."),
        ("Pelle", "Vi följer utvecklingen inom artificiell intelligens och dess roll i klimatarbetet, nya tekniska lösningar för att minska utsläpp, och hur samhället anpassar sig till klimatförändringarna."),
        ("Lisa", "Men vi glömmer inte bort den mänskliga faktorn. Hur påverkar ny teknik våra liv, våra jobb, och våra möjligheter att leva mer hållbart?"),
        ("Pelle", "Våra källor kommer från svenska medier som SVT, DN och SvD, europeiska nyhetskällor som Euronews och Politico Europe, samt internationella giganter som BBC och Reuters."),
        ("Lisa", "Transparens är viktigt för oss - vi anger alltid vilka källor våra nyheter kommer från så att ni kan läsa mer om det som intresserar er."),
        ("Pelle", "Och här kommer några exempel på vad ni kan förvänta er. I veckan har vi till exempel sett hur artificiell intelligens nu används för att optimera vindkraftsparker i Östersjön, vilket kan öka energiproduktionen med upp till 15 procent."),
        ("Lisa", "Vi ger er alltid senaste nytt. Igår rapporterade till exempel Reuters om ett genombrott inom batteriåtervinning som kan minska koboltbehovet med 70 procent. Sådana nyheter når er samma dag här hos oss."),
        ("Pelle", "Vare sig det handlar om genombrott inom förnybar energi, nya AI modeller som kan hjälpa miljöarbetet, eller politiska beslut som påverkar klimatet, så håller vi er uppdaterade."),
        ("Lisa", "Så vad kan ni förvänta er framöver? Måndag till fredag fokuserar vi på veckans stora nyheter och utvecklingar. Helger blir mer reflekterande med djupare analys."),
        ("Pelle", "Men Lisa, varför tio minuter? Varför inte en timme? Eller bara ett par minuter?"),
        ("Lisa", "Jo, vi tror att tio minuter är alldeles lagom. Tio minuter har alla tid med, det blir inte för långt, det blir inte för kort. Det blir alldeles lagom. Vi tror våra lyssnare kommer hålla med oss."),
        ("Pelle", "Och glöm inte bort att prenumerera på vår huvudpodcast Människa Maskin Miljö för djupare dykningar i dessa ämnen, där tar vi oss tid att verkligen utforska hur allt hänger ihop. Det handlar om den Gröna Tråden."),
        ("Lisa", "Vi på MMM Senaste Nytt kommer här varje dag, samma tid, med nyheter som formar vår framtid. För det är just det det handlar om. Hur vi tillsammans navigerar i en värld där teknik, mänsklighet och miljö ständigt påverkar varandra."),
        ("Pelle", "Så välkomna till MMM Senaste Nytt! Vi ses här imorgon med dagens viktigaste nyheter från världen av människa, maskin och miljö."),
        ("Lisa", "Ha det bra tills dess!")
    ]
    
    print("🎙️ Skapar premiäravsnitt MMM Senaste Nytt...")
    print(f"📊 Totalt {len(dialogue)} repliker att generera")
    
    audio_files = []
    total_cost = 0
    
    for i, (speaker, text) in enumerate(dialogue):
        print(f"\n🎤 Genererar replik {i+1}/{len(dialogue)}: {speaker}")
        print(f"Text: {text[:60]}{'...' if len(text) > 60 else ''}")
        
        # Välj rätt röst
        voice = lisa_voice if speaker == "Lisa" else pelle_voice
        
        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Spara individuell replik
            filename = f"premiere_{i+1:02d}_{speaker.lower()}_{int(time.time())}.mp3"
            filepath = f"audio/{filename}"
            
            with open(filepath, "wb") as out:
                out.write(response.audio_content)
            
            audio_files.append((speaker, filepath, text))
            
            # Kostnadsberäkning
            cost = len(text) * 0.000004  # $4 per 1M chars for Chirp3-HD
            total_cost += cost
            
            print(f"✅ Sparat: {filename}")
            print(f"💰 Kostnad: ${cost:.4f}")
            
            # Kort paus mellan anrop för att vara snäll mot API:et
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Fel vid generering av replik {i+1}: {e}")
            continue
    
    print(f"\n🎉 Klar! Genererade {len(audio_files)} audio-filer")
    print(f"💰 Total kostnad: ${total_cost:.4f}")
    
    # Skapa instruktioner för Audacity
    create_audacity_instructions(audio_files)
    
    return audio_files

def create_audacity_instructions(audio_files):
    """Skapar instruktioner för hur filerna ska läggas ihop i Audacity"""
    
    instructions = """
# 🎧 AUDACITY INSTRUKTIONER - MMM Senaste Nytt Premiär

## Importordning och timing:

1. **INTRO MUSIK** (15-20 sekunder)
   - Lägg till din intro-musik först
   
"""
    
    segment_counter = 1
    for i, (speaker, filepath, text) in enumerate(audio_files):
        # Lägg till bryggmusik efter vissa repliker
        if i == 3:  # Efter Pelle's första långa replik
            instructions += f"\n2. **BRYGGA MUSIK** (5-8 sekunder)\n"
            segment_counter += 1
        elif i == 7:  # Efter källornämning
            instructions += f"\n{segment_counter}. **BRYGGA MUSIK** (5-8 sekunder)\n"
            segment_counter += 1
        elif i == 11:  # Efter exempel-sektionen
            instructions += f"\n{segment_counter}. **BRYGGA MUSIK** (5-8 sekunder)\n"
            segment_counter += 1
        
        instructions += f"{segment_counter}. **{speaker.upper()}**: {filepath}\n"
        instructions += f"   Text: \"{text[:100]}{'...' if len(text) > 100 else ''}\"\n\n"
        segment_counter += 1
    
    instructions += f"""
{segment_counter}. **OUTRO MUSIK** (20-25 sekunder med fade out)

## 🎛️ Produktionstips:

### Röstjusteringar:
- **Lisa (Gacrux)**: Eventuellt lätt höjning av bas för varmare ton
- **Pelle (Charon)**: Eventuellt lätt kompression för jämnare volym

### Övergångar:
- Lägg till 0.5-1 sekunds tystnad mellan repliker
- Cross-fade mellan röster för naturligare flöde
- Bryggmusik ska fade in/out smidigt

### Slutbehandling:
- Normalisera hela avsnittet till -16 LUFS för podcast-standard
- Lägg till subtle EQ om det behövs
- Exportera som stereo MP3, 128kbps eller högre

Estimerad slutlengd: 8-10 minuter
"""
    
    with open("AUDACITY_INSTRUKTIONER.md", "w", encoding="utf-8") as f:
        f.write(instructions)
    
    print("📋 Skapat: AUDACITY_INSTRUKTIONER.md")

if __name__ == "__main__":
    audio_files = create_premiere_episode()
    
    print("\n🚀 Nästa steg:")
    print("1. Öppna Audacity")
    print("2. Följ instruktionerna i AUDACITY_INSTRUKTIONER.md")  
    print("3. Lägg till musik enligt markörerna")
    print("4. Exportera som färdig podcast!")
    
    print(f"\n📁 Alla filer finns i audio/ mappen")
    print("🎵 Nu behöver du bara din intro/outro musik!")