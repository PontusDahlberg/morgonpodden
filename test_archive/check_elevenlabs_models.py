#!/usr/bin/env python3
import requests

import os

api_key = os.getenv('ELEVENLABS_API_KEY')
if not api_key:
    print("❌ ELEVENLABS_API_KEY environment variable not found!")
    exit(1)

# Kolla tillgängliga modeller
print('🔍 Kollar tillgängliga ElevenLabs modeller...')
headers = {
    'Accept': 'application/json',
    'xi-api-key': api_key
}

response = requests.get('https://api.elevenlabs.io/v1/models', headers=headers)

if response.status_code == 200:
    models = response.json()
    print('✅ Tillgängliga modeller:')
    print()
    for model in models['models']:
        name = model['model_id']
        description = model.get('name', 'N/A')
        languages = model.get('languages', [])
        print(f'🤖 {name}')
        print(f'   Namn: {description}')
        print(f'   Språk: {languages[:5] if len(languages) > 5 else languages}')
        
        # Kolla capabilities
        if 'can_do_text_guided_voice_conversion' in model:
            voice_conv = model['can_do_text_guided_voice_conversion']
            print(f'   Voice conversion: {voice_conv}')
        if 'can_do_voice_conversion' in model:
            voice_conv2 = model['can_do_voice_conversion']
            print(f'   Röstkonvertering: {voice_conv2}')
        print('---')
else:
    print(f'❌ Error: {response.status_code}')
    print(response.text)

# Testa också att kolla nya röster
print()
print('🔍 Kollar efter nya svenska röster...')

response2 = requests.get('https://api.elevenlabs.io/v1/voices', headers=headers)

if response2.status_code == 200:
    voices = response2.json()
    
    # Filtrera svenska röster och visa creation date
    swedish_voices = []
    for voice in voices['voices']:
        name = voice['name']
        voice_id = voice['voice_id']
        category = voice.get('category', 'N/A')
        labels = voice.get('labels', {})
        accent = labels.get('accent', 'N/A')
        
        # Leta efter svenska/nordiska indikatorer
        if any(keyword in name.lower() for keyword in ['swedish', 'sverige', 'stockholm', 'sanna', 'nordic', 'scandinavian']) or accent.lower() in ['stockholm', 'swedish', 'nordic', 'scandinavian']:
            creation_date = voice.get('date_created', 'N/A')
            swedish_voices.append((name, voice_id, category, accent, creation_date))
    
    print('🇸🇪 Svenska/Nordiska röster (med datum):')
    for name, voice_id, category, accent, date in swedish_voices:
        print(f'✅ {name}')
        print(f'   ID: {voice_id}')
        print(f'   Kategori: {category}')
        print(f'   Accent: {accent}')
        print(f'   Skapad: {date}')
        print()
else:
    print(f'❌ Voice Error: {response2.status_code}')
