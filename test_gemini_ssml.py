#!/usr/bin/env python3
"""
Test script to explore if Gemini models can generate SSML instructions
for emotional variation in Google Cloud TTS.
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gemini_ssml_generation():
    """Test if Gemini can generate SSML with emotional instructions."""
    
    # Set up Gemini API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment variables")
        return None
    
    genai.configure(api_key=api_key)
    
    # Initialize Gemini model
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Test script from our podcast
    test_script = """
    Hej och välkomna till vår morgonpodd! 
    
    Idag ska vi prata om något verkligen spännande - vi har hittat en ny artist som kommer att förändra hela musikscenen. 
    
    Men först... lite mer seriösa nyheter. Situationen i världen just nu kräver vår uppmärksamhet.
    
    Det här är verkligen viktigt att komma ihåg, alla lyssnare!
    
    Men nu tillbaka till den glada stämningen - vi avslutar med veckans bästa låt!
    """
    
    prompt = f"""
    Du är expert på att konvertera podcastmanus till SSML-kod (Speech Synthesis Markup Language) som kan användas med Google Cloud Text-to-Speech för att skapa emotionella variationer.

    Konvertera följande svenska podcastmanus till välformulerad SSML-kod:

    {test_script}

    Använd dessa SSML-taggar strategiskt:
    - <prosody rate="fast/medium/slow" pitch="+4st/+2st/default/-2st" volume="loud/medium/soft"> för tempo, tonhöjd och volym
    - <emphasis level="strong/moderate"> för betoning  
    - <break time="1s/500ms"/> för pauser
    - <speak> som wrapper

    Variera stilen intelligent baserat på innehållet:
    - Energisk och snabb för välkomnande (rate="fast", pitch="+2st")
    - Spännande för musiknyheter (pitch="+4st", emphasis)
    - Allvarlig för seriösa nyheter (rate="slow", pitch="-2st")
    - Stark betoning för viktiga poänger (emphasis level="strong")
    - Glad och medel för avslutning (rate="medium", pitch="+1st")

    Ge mig den kompletta SSML-koden som är redo att användas:
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"❌ Error with Gemini API: {e}")
        return None

def main():
    print("🤖 Testing Gemini for SSML generation...\n")
    
    # Test Gemini's ability to generate emotional SSML
    ssml_result = test_gemini_ssml_generation()
    
    if ssml_result:
        print("✅ Gemini generated SSML with emotional variations:")
        print("="*60)
        print(ssml_result)
        print("="*60)
        print("\n💡 Key Insight:")
        print("Gemini CAN help generate intelligent SSML markup,")
        print("but we still need Google Cloud TTS WaveNet voices")  
        print("(not Chirp3-HD) to actually synthesize SSML.")
        print("\nThis could be our optimal workflow:")
        print("1. Gemini generates emotionally-aware SSML")
        print("2. WaveNet voices synthesize with SSML support")
        print("3. Cost: $0.016/1000 chars (still 11x cheaper than ElevenLabs)")
        
        # Save the generated SSML
        with open('gemini_generated_ssml_sample.txt', 'w', encoding='utf-8') as f:
            f.write(ssml_result)
        print(f"\n📁 Saved to: gemini_generated_ssml_sample.txt")
        
    else:
        print("❌ Could not test Gemini for SSML generation")
        print("Check your GEMINI_API_KEY in .env file")

if __name__ == "__main__":
    main()