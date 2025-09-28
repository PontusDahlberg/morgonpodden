#!/usr/bin/env python3
import requests

import os

api_key = os.getenv('ELEVENLABS_API_KEY')
if not api_key:
    print("❌ ELEVENLABS_API_KEY environment variable not found!")
    exit(1)
headers = {'Accept': 'application/json', 'xi-api-key': api_key}

print('🔍 Kollar tillgängliga ElevenLabs modeller...')
response = requests.get('https://api.elevenlabs.io/v1/models', headers=headers)

if response.status_code == 200:
    models = response.json()
    print('✅ Tillgängliga modeller:')
    print()
    
    for model in models:
        name = model.get('model_id', 'N/A')
        description = model.get('name', 'N/A')
        can_use_style = model.get('can_use_style', False)
        can_tts = model.get('can_do_text_to_speech', False)
        
        print(f'🤖 {name}')
        print(f'   Namn: {description}')
        print(f'   Kan använda style: {can_use_style}')
        print(f'   Text-to-speech: {can_tts}')
        if 'description' in model and model['description']:
            desc = model['description']
            if len(desc) > 100:
                desc = desc[:100] + '...'
            print(f'   Beskrivning: {desc}')
        print('---')
        
    # Leta efter V3 och andra avancerade modeller
    v3_models = []
    for model in models:
        model_id = model.get('model_id', '').lower()
        if 'v3' in model_id or 'turbo' in model_id or model.get('can_use_style', False):
            v3_models.append(model)
            
    if v3_models:
        print()
        print('🚀 Avancerade modeller (V3/Style support):')
        for model in v3_models:
            model_name = model.get('model_id', 'N/A')
            display_name = model.get('name', 'N/A')
            style_support = model.get('can_use_style', False)
            print(f'✨ {model_name} - {display_name}')
            print(f'   Style support: {style_support}')
            if style_support:
                print('   ⭐ DENNA HAR EMOTIONAL TAGGING!')
    else:
        print()
        print('ℹ️ Inga V3 modeller med style support hittade')
        
else:
    print(f'❌ Error: {response.status_code}')
