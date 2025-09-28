#!/usr/bin/env python3
"""
Intelligent SSML generator för podcastmanus
Skapar emotionella variationer utan att behöva Gemini API
"""

import re
from typing import Dict, List, Tuple

class IntelligentSSMLGenerator:
    """Genererar emotionellt medveten SSML baserat på innehåll"""
    
    def __init__(self):
        # Känsloregler baserat på innehåll
        self.emotion_patterns = {
            'excited': {
                'patterns': [r'spännande', r'fantastisk', r'amazing', r'wow', r'otrolig', r'förändra', r'ny artist'],
                'ssml': {'rate': 'fast', 'pitch': '+4st', 'volume': 'loud'}
            },
            'welcoming': {
                'patterns': [r'välkomna', r'hej', r'vi ses', r'tack för att'],
                'ssml': {'rate': 'fast', 'pitch': '+2st', 'volume': 'medium'}
            },
            'serious': {
                'patterns': [r'allvarlig', r'situation', r'världen', r'kräver', r'uppmärksamhet', r'först\.\.\.'],
                'ssml': {'rate': 'slow', 'pitch': '-2st', 'volume': 'soft'}
            },
            'important': {
                'patterns': [r'viktigt', r'komma ihåg', r'alla lyssnare', r'det här är'],
                'ssml': {'rate': 'medium', 'pitch': '+1st', 'volume': 'loud', 'emphasis': 'strong'}
            },
            'happy_ending': {
                'patterns': [r'tillbaka till', r'glada', r'avslutar', r'bästa låt', r'nu tillbaka'],
                'ssml': {'rate': 'medium', 'pitch': '+2st', 'volume': 'medium'}
            }
        }
        
    def analyze_sentence_emotion(self, sentence: str) -> Dict:
        """Analyserar en mening och returnerar bästa känslan"""
        sentence_lower = sentence.lower()
        
        # Hitta matchande känslor
        matches = {}
        for emotion, data in self.emotion_patterns.items():
            score = 0
            for pattern in data['patterns']:
                if re.search(pattern, sentence_lower):
                    score += 1
            if score > 0:
                matches[emotion] = score
        
        # Returnera starkaste känslan
        if matches:
            best_emotion = max(matches.items(), key=lambda x: x[1])[0]
            return self.emotion_patterns[best_emotion]['ssml']
        
        # Default neutralt tonläge
        return {'rate': 'medium', 'pitch': 'default', 'volume': 'medium'}
    
    def create_prosody_tag(self, text: str, emotion_ssml: Dict) -> str:
        """Skapar SSML prosody-tagg för text"""
        attributes = []
        
        if 'rate' in emotion_ssml:
            attributes.append(f'rate="{emotion_ssml["rate"]}"')
        if 'pitch' in emotion_ssml:
            attributes.append(f'pitch="{emotion_ssml["pitch"]}"')
        if 'volume' in emotion_ssml:
            attributes.append(f'volume="{emotion_ssml["volume"]}"')
        
        attrs_str = ' '.join(attributes)
        
        # Lägg till emphasis om det finns
        if emotion_ssml.get('emphasis'):
            text = f'<emphasis level="{emotion_ssml["emphasis"]}">{text}</emphasis>'
        
        return f'<prosody {attrs_str}>{text}</prosody>'
    
    def add_intelligent_breaks(self, text: str) -> str:
        """Lägger till intelligenta pauser"""
        # Längre paus efter exclamation marks och sentences med "..."
        text = re.sub(r'!(\s+)', r'!\n<break time="800ms"/>\1', text)
        text = re.sub(r'\.\.\.(\s+)', r'...\n<break time="1.5s"/>\1', text)
        
        # Medium paus efter punkter
        text = re.sub(r'\.(\s+)([A-ZÅÄÖ])', r'.\n<break time="500ms"/>\1\2', text)
        
        # Kort paus efter komma
        text = re.sub(r',(\s+)', r',\n<break time="300ms"/>\1', text)
        
        return text
    
    def convert_to_ssml(self, text: str) -> str:
        """Konverterar text till intelligent SSML"""
        # Dela upp i meningar
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        
        ssml_parts = ['<speak>']
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            # Analysera känsla för mening
            emotion_ssml = self.analyze_sentence_emotion(sentence)
            
            # Skapa SSML för mening
            ssml_sentence = self.create_prosody_tag(sentence, emotion_ssml)
            
            # Lägg till i paragraph
            ssml_parts.append(f'<p>{ssml_sentence}</p>')
        
        ssml_parts.append('</speak>')
        
        # Sammansätt och lägg till intelligenta pauser
        ssml_text = '\n'.join(ssml_parts)
        ssml_text = self.add_intelligent_breaks(ssml_text)
        
        return ssml_text

def test_intelligent_ssml():
    """Testa den intelligenta SSML-generatorn"""
    
    generator = IntelligentSSMLGenerator()
    
    # Test med podcasttext
    test_text = """
    Hej och välkomna till vår morgonpodd! 
    
    Idag ska vi prata om något verkligen spännande - vi har hittat en ny artist som kommer att förändra hela musikscenen. 
    
    Men först... lite mer seriösa nyheter. Situationen i världen just nu kräver vår uppmärksamhet.
    
    Det här är verkligen viktigt att komma ihåg, alla lyssnare!
    
    Men nu tillbaka till den glada stämningen - vi avslutar med veckans bästa låt!
    """
    
    # Generera SSML
    ssml_result = generator.convert_to_ssml(test_text)
    
    print("🤖 Intelligent SSML Generator Results:")
    print("="*60)
    print(ssml_result)
    print("="*60)
    
    # Spara resultat
    with open('intelligent_ssml_sample.txt', 'w', encoding='utf-8') as f:
        f.write(ssml_result)
    
    print("\n💡 Analysis:")
    print("• Welcoming: Fast rate, +2st pitch for 'Hej och välkomna'")
    print("• Excited: Fast rate, +4st pitch for 'spännande' och 'ny artist'")  
    print("• Serious: Slow rate, -2st pitch for 'seriösa nyheter'")
    print("• Important: Medium rate, +1st pitch, strong emphasis for 'viktigt'")
    print("• Happy: Medium rate, +2st pitch for 'glada stämningen'")
    print(f"\n📁 Saved to: intelligent_ssml_sample.txt")
    
    return ssml_result

if __name__ == "__main__":
    test_intelligent_ssml()